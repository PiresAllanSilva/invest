
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF

st.set_page_config(page_title="Simulador Comparativo de Investimentos", layout="wide")

def calcular_aliquota_ir(dias):
    if dias <= 180:
        return 0.225
    elif dias <= 360:
        return 0.20
    elif dias <= 720:
        return 0.175
    else:
        return 0.15

def calcular_investimento(valor_inicial, deposito_mensal, taxa_juros, tipo_juros, anos, inflacao=0.0,
                           inicio_resgate=None, valor_resgate=0.0):
    meses = anos * 12
    dias_totais = anos * 365
    juros_mensal = taxa_juros / 100 if tipo_juros == "Mensal" else (1 + taxa_juros / 100) ** (1/12) - 1
    inflacao_mensal = (1 + inflacao / 100) ** (1/12) - 1 if inflacao > 0 else 0.0

    saldo = valor_inicial
    saldo_corrigido = valor_inicial
    total_investido = valor_inicial
    resgatado = 0
    saldos = []

    for mes in range(meses + 1):
        if mes > 0:
            saldo *= (1 + juros_mensal)
            if inicio_resgate and mes >= inicio_resgate and valor_resgate > 0:
                saque = min(valor_resgate, saldo)
                saldo -= saque
                resgatado += saque
            saldo += deposito_mensal
            total_investido += deposito_mensal

        saldo_corrigido = saldo / ((1 + inflacao_mensal) ** mes) if inflacao > 0 else saldo
        saldos.append({
            "Mês": mes,
            "Valor Bruto (R$)": round(saldo, 2),
            "Valor Corrigido (R$)": round(saldo_corrigido, 2)
        })

    df = pd.DataFrame(saldos)

    rendimento_bruto = saldo - total_investido
    aliquota_ir = calcular_aliquota_ir(dias_totais)
    imposto = rendimento_bruto * aliquota_ir
    lucro_liquido = rendimento_bruto - imposto

    resumo = {
        "Total Investido (R$)": round(total_investido, 2),
        "Valor Bruto Final (R$)": round(saldo, 2),
        "Lucro Bruto (R$)": round(rendimento_bruto, 2),
        "Imposto Estimado (R$)": round(imposto, 2),
        "Lucro Líquido (R$)": round(lucro_liquido, 2),
        "Valor Corrigido pela Inflação (R$)": round(saldo_corrigido, 2),
        "Total Resgatado (R$)": round(resgatado, 2)
    }

    return df, resumo

def gerar_pdf(df1, resumo1, df2, resumo2):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Resumo Comparativo de Investimentos", ln=True, align="C")
    pdf.set_font("Arial", size=12)

    pdf.ln(10)
    pdf.cell(200, 10, "Cenário 1", ln=True)
    for k, v in resumo1.items():
        pdf.cell(200, 10, f"{k}: R$ {v}", ln=True)

    pdf.ln(10)
    pdf.cell(200, 10, "Cenário 2", ln=True)
    for k, v in resumo2.items():
        pdf.cell(200, 10, f"{k}: R$ {v}", ln=True)

    output = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    output.write(pdf_bytes)
    output.seek(0)
    return output

st.title("📊 Simulador Comparativo de Investimentos")

with st.sidebar:
    st.header("Configuração Base")
    valor_inicial = st.number_input("💰 Valor inicial (R$)", 0.0, value=1000.0, step=100.0)
    deposito_mensal = st.number_input("📥 Depósito mensal (R$)", 0.0, value=500.0, step=50.0)
    taxa_juros = st.number_input("📈 Juros (% ao ano ou mês)", 0.0, value=10.0)
    tipo_juros = st.radio("Tipo de juros", ["Mensal", "Anual"])
    anos = st.slider("⏳ Anos de investimento", 1, 50, 35)
    inflacao = st.number_input("📉 Inflação anual (%)", 0.0, 20.0, value=4.5)

    st.header("Cenário 1: Sem Resgate")
    inicio_resgate1 = None
    valor_resgate1 = 0.0

    st.header("Cenário 2: Resgate após 30 anos")
    inicio_resgate2 = 30 * 12  # 30 anos em meses
    valor_resgate2 = st.number_input("💸 Valor de resgate mensal após 30 anos (R$)", 0.0, value=500.0, step=50.0)

df1, resumo1 = calcular_investimento(
    valor_inicial, deposito_mensal, taxa_juros, tipo_juros, anos, inflacao, inicio_resgate1, valor_resgate1
)

df2, resumo2 = calcular_investimento(
    valor_inicial, deposito_mensal, taxa_juros, tipo_juros, anos, inflacao, inicio_resgate2, valor_resgate2
)

st.subheader("📈 Comparação Gráfica entre os Cenários")
fig, ax = plt.subplots()
ax.plot(df1["Mês"], df1["Valor Bruto (R$)"], label="Cenário 1 - Sem Resgate")
ax.plot(df2["Mês"], df2["Valor Bruto (R$)"], label="Cenário 2 - Resgate após 30 anos")
ax.set_xlabel("Meses")
ax.set_ylabel("Valor Bruto (R$)")
ax.set_title("Evolução dos Investimentos")
ax.legend()
st.pyplot(fig)

st.subheader("📋 Resumo dos Cenários")
col1, col2 = st.columns(2)
with col1:
    st.write("### Cenário 1 - Sem Resgate")
    st.write(pd.DataFrame([resumo1]).T.rename(columns={0: "Valor"}))
with col2:
    st.write("### Cenário 2 - Com Resgate após 30 anos")
    st.write(pd.DataFrame([resumo2]).T.rename(columns={0: "Valor"}))

pdf = gerar_pdf(df1, resumo1, df2, resumo2)
st.download_button("📄 Baixar resumo em PDF", data=pdf, file_name="resumo_comparativo.pdf", mime="application/pdf")
