import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Roleta Mestre")

# --------------------- Classe de análise ---------------------
class AnalistaRoleta:
    def __init__(self):
        self.historico = []

    def adicionar_numero(self, numero):
        if numero is not None:
            self.historico.append(numero)

    def analisar_estrategia(self):
        if not self.historico:
            return "Sem números no histórico."
        df = pd.DataFrame(self.historico, columns=["Número"])
        frequencia = df["Número"].value_counts().reset_index()
        frequencia.columns = ["Número", "Frequência"]
        frequencia = frequencia.sort_values("Número")
        return frequencia

# --------------------- Função de login ---------------------
def check_password():
    senha_correta = "1234"
    senha = st.text_input("Senha:", type="password")
    if senha != senha_correta:
        st.warning("Senha incorreta.")
        return False
    return True

# --------------------- Inicialização ---------------------
if "analista" not in st.session_state:
    st.session_state.analista = AnalistaRoleta()

analista = st.session_state.analista

# --------------------- Layout principal ---------------------
st.title("Roleta Mestre")

# Inserir números por colar
entrada_colar = st.text_area(
    "Cole os números separados por vírgula ou espaço:",
    placeholder="Ex: 17, 25, 3 ou 17 25 3"
)

if st.button("Adicionar números colados"):
    if entrada_colar:
        # Substitui espaços por vírgulas e remove duplas vírgulas
        entrada_colar = entrada_colar.replace(" ", ",")
        entrada_colar = ",".join([x for x in entrada_colar.split(",") if x != ""])
        numeros = [int(x) for x in entrada_colar.split(",") if x.isdigit()]
        for n in numeros:
            if 0 <= n <= 36:
                analista.adicionar_numero(n)
        st.success(f"Números adicionados: {numeros}")

# Inserir números manualmente
st.subheader("Adicionar número manualmente:")
col1, col2, col3 = st.columns(3)
for i in range(0, 37):
    if col1.button(str(i)) and 0 <= i <= 36:
        analista.adicionar_numero(i)

# --------------------- Histórico ---------------------
st.subheader("Histórico de números")
st.write(analista.historico)

if st.button("Limpar histórico"):
    st.session_state.analista.historico = []
    st.success("Histórico limpo.")

# --------------------- Análise ---------------------
st.subheader("Análise de Estratégia")
frequencia = analista.analisar_estrategia()
st.dataframe(frequencia)

# --------------------- Gráfico ---------------------
if not frequencia.empty:
    fig = px.bar(frequencia, x="Número", y="Frequência", text="Frequência")
    fig.update_traces(marker_color="red")
    st.plotly_chart(fig, use_container_width=True)
