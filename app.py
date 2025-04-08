import io
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulador Comparativo de Investimentos", layout="wide")

# Converter para taxa mensal se necessário
def converter_para_mensal(taxa, tipo):
    if tipo == "Anual":
        return (1 + taxa / 100) ** (1/12) - 1
    else:
        return taxa / 100

def calcular_aliquota_ir(dias):
    if dias <= 180:
        return 0.225
    elif dias <= 360:
        return 0.20
    elif dias <= 720:
        return 0.175
    else:
        return 0.15

def calcular_investimento(nome_cenario, valor_inicial, deposito_mensal, taxa_juros, tipo_juros, anos, inflacao=0.0,
                          inicio_resgate=None, valor_resgate=0.0):
    meses = anos * 12
    dias_totais = anos * 365
    juros_mensal = taxa_juros / 100 if tipo_juros == "Mensal" else (1 + taxa_juros / 100) ** (1/12) - 1
    inflacao_mensal = (1 + inflacao / 100) ** (1/12) - 1 if inflacao > 0 else 0.0

    saldo = valor_inicial
    total_investido = valor_inicial
    resgatado = 0
    resgatado_corrigido = 0
    saldos = []

    for mes in range(meses + 1):
        if mes > 0:
            saldo *= (1 + juros_mensal)
            if inicio_resgate and mes >= inicio_resgate and valor_resgate > 0:
                saque = min(valor_resgate, saldo)
                saldo -= saque
                resgatado += saque
                saque_corrigido = saque / ((1 + inflacao_mensal) ** mes)
                resgatado_corrigido += saque_corrigido
            saldo += deposito_mensal
            total_investido += deposito_mensal

        saldo_corrigido_atual = saldo / ((1 + inflacao_mensal) ** mes) if inflacao > 0 else saldo

        saldos.append({
            "Mês": mes,
            "Cenário": nome_cenario,
            "Valor Bruto (R$)": round(saldo, 2),
            "Valor Corrigido (R$)": round(saldo_corrigido_atual, 2)
        })

    df = pd.DataFrame(saldos)

    rendimento_bruto = saldo - total_investido
    aliquota_ir = calcular_aliquota_ir(dias_totais)
    imposto = rendimento_bruto * aliquota_ir
    lucro_liquido = rendimento_bruto - imposto
    valor_corrigido_final = df["Valor Corrigido (R$)"].iloc[-1]

    resumo = {
        "Cenário": nome_cenario,
        "Total Investido (R$)": round(total_investido, 2),
        "Valor Bruto Final (R$)": round(saldo, 2),
        "Lucro Bruto (R$)": round(rendimento_bruto, 2),
        "Imposto Estimado (R$)": round(imposto, 2),
        "Lucro Líquido (R$)": round(lucro_liquido, 2),
        "Valor Corrigido pela Inflação (R$)": round(valor_corrigido_final, 2),
        "Total Resgatado (R$)": round(resgatado, 2),
        "Total Resgatado Corrigido (R$)": round(resgatado_corrigido, 2)
    }

    return df, resumo

# Sidebar
st.sidebar.subheader("Parâmetros da Simulação")
valor_inicial = st.sidebar.number_input("Valor Inicial (R$)", value=1000.0, step=100.0)
deposito_mensal = st.sidebar.number_input("Depósito Mensal (R$)", value=500.0, step=100.0)

st.sidebar.markdown("---")
st.sidebar.subheader("Taxas de Rendimento")
taxa_de_juros = st.sidebar.number_input("Taxa de Juros (%)", value=1.0, step=0.1)
tipo_taxa = st.sidebar.selectbox("Tipo de Taxa", ["Mensal", "Anual"], index=0)


st.sidebar.markdown("---")
st.sidebar.subheader("Período de Investimento")
anos = st.sidebar.slider("Anos de Investimento", 1, 100, value=50)
inflacao = st.sidebar.slider("Inflação Anual (%)", 0.0, 20.0, value=3.0, step=0.1)

st.sidebar.markdown("---")
st.sidebar.subheader("Definição dos resgates")
valor_resgate = st.sidebar.number_input(
    "Valor de Resgate Mensal", value=10000.0, step=100.0
)

inicio_resgate_anos = st.sidebar.slider(
    "Início dos Saques (anos)", min_value=1, max_value=anos, value=25
)
resgate_anos = inicio_resgate_anos

# Cálculo do valor corrigido
inflacao_mensal = (1 + inflacao / 100) ** (1/12) - 1 if inflacao > 0 else 0.0
fator_inflacao = (1 + inflacao_mensal) ** (inicio_resgate_anos * 12)
valor_resgate_corrigido = valor_resgate / fator_inflacao if fator_inflacao > 0 else valor_resgate

st.sidebar.markdown("---")
st.sidebar.subheader("Poder de compra comparado")
st.sidebar.markdown(
    f"💡 Valor corrigido em **{fator_inflacao*resgate_anos:,.2f}%** acumulados por **{resgate_anos} anos**: R$ {valor_resgate_corrigido:,.2f}", unsafe_allow_html=True
)

# Cálculo dos cenários
df1, resumo1 = calcular_investimento("Descrição dos valores sem saques", valor_inicial, deposito_mensal, taxa_de_juros, tipo_taxa, anos)
df3, resumo3 = calcular_investimento(f"Descrição dos valores com saques mensais a partir de {resgate_anos} anos", valor_inicial, deposito_mensal, taxa_de_juros, tipo_taxa, anos, inflacao, resgate_anos * 12, valor_resgate)

df_total = pd.concat([df1, df3], ignore_index=True)
df_total["Ano"] = df_total["Mês"] // 12
df_total["Valor Final (mil)"] = df_total["Valor Corrigido (R$)"] / 1000
resumo_df = pd.DataFrame([resumo1, resumo3])

# Página principal

st.title("📊 Simulador Comparativo de Investimentos")
st.markdown("Personalize os parâmetros no menu lateral e compare o desempenho dos investimentos.")

# Tabela de resumo
st.subheader("📋 Resumo dos Cenários")
resumo_df.index = resumo_df['Cenário']
showing_dataframe = resumo_df.iloc[:, 1:].T

def df_to_html_centered(df):
    return df.style\
        .format("R$ {:,.2f}")\
        .set_properties(**{"text-align": "center"})\
        .set_table_styles(
            [{"selector": "th", "props": [("text-align", "center")]}]
        )\
        .to_html()

html_table = df_to_html_centered(showing_dataframe)
# Centraliza horizontalmente e aplica scroll se necessário
st.markdown(
    f"""
    <div style='
        display: flex;
        justify-content: center;
        padding: 1rem;
    '>
        <div style='
            overflow-x: auto;
            max-width: 100%;
        '>
            {html_table}
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("---")
st.subheader("📈 Evolução dos Investimentos (Valor Corrigido)")
fig, ax = plt.subplots(figsize=(10, 6))

# Prepara os dados
df_plot = df_total.copy()
df_plot["Ano"] = df_plot["Mês"] // 12
df_plot["Valor Corrigido (mil R$)"] = df_plot["Valor Corrigido (R$)"] / 1000

# Cria a figura e define fundo #0e1117 em todos os níveis
fig, ax = plt.subplots(figsize=(12, 6), facecolor="#0e1117")  # fundo do canvas
ax.set_facecolor("#0e1117")  # fundo da área do gráfico

# Linha branca ao redor da área do gráfico
for spine in ax.spines.values():
    spine.set_edgecolor("white")
    spine.set_linewidth(1.2)
    
# Plotagem por cenário com cores personalizadas
for cenario in df_plot["Cenário"].unique():
    dados = df_plot[df_plot["Cenário"] == cenario]

    # Cores específicas
    if cenario == "Cenário 1":
        cor = "white"
    elif cenario == f"Descrição dos valores com saques mensais a partir de {resgate_anos} anos":
        cor = "red"
    elif cenario == "Descrição dos valores sem saques":
        cor = "lightgray"
    else:
        cor = "cyan"

    sns.lineplot(data=dados, x="Ano", y="Valor Corrigido (mil R$)", label=cenario,
                 ax=ax, marker="o", color=cor, linewidth=2)

# Estilização
ax.set_xlabel("Anos", color="white")
ax.set_ylabel("Valor Corrigido (milhares de reais)", color="white")
ax.legend(facecolor="#0e1117", labelcolor="white", title_fontsize=11, fontsize=10)
ax.tick_params(colors="white")
ax.grid(False)

# Remove bordas excessivas
plt.tight_layout()


# ✅ Salva o gráfico como imagem com fundo correto
buf = io.BytesIO()
fig.savefig(buf, format="png", facecolor="#0e1117", bbox_inches="tight")
buf.seek(0)

# ✅ Mostra no Streamlit com fundo corrigido
st.image(buf)

# Mostra no Streamlit
#st.pyplot(fig)


# Botão para exportar
st.subheader("📥 Exportar Resultados")
export_button = st.button("📥 Baixar Excel com Tabela e Resumo")

if export_button:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_total.to_excel(writer, index=False, sheet_name='Simulação')
        resumo_df.to_excel(writer, index=False, sheet_name='Resumo')

    output.seek(0)
    st.download_button(
        label="📄 Download do Excel",
        data=output,
        file_name="simulacao_investimentos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.sidebar.markdown("---")
st.subheader("📈 Tabela intetiva")
st.dataframe(showing_dataframe, use_container_width=False)
