# app_roleta.py
import streamlit as st

import plotly.express as px

# Configuração da página
st.set_page_config(layout="wide", page_title="Roleta Mestre")

# --- Classe Analista ---
class AnalistaRoleta:
    def __init__(self):
        self.historico = []
        self.CILINDRO_EUROPEU = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
        self.VIZINHOS = self._calcular_vizinhos()
        self.CAVALOS_TRIPLOS = {
            0: [3, 7], 1: [4, 8], 2: [5, 9], 3: [6, 0], 4: [7, 1],
            5: [8, 2], 6: [9, 3], 7: [0, 4], 8: [1, 5], 9: [2, 6]
        }
        self.JUNCAO_TERMINAIS = {0, 1, 3, 4}
        self.DISFARCADOS = {
            0: {11, 19, 22, 28, 33}, 1: {12, 23, 29, 32, 34},
            2: {11, 13, 24, 31, 35}, 3: {12, 14, 21, 25, 26, 36},
            4: {13, 15, 22, 26, 28, 31}, 5: {14, 16, 23, 27, 32},
            6: {15, 17, 24, 28, 33}, 7: {16, 18, 25, 29, 34},
            8: {17, 19, 24, 26, 35}, 9: {18, 27, 33, 36}
        }

    def _calcular_vizinhos(self):
        vizinhos = {}
        tamanho = len(self.CILINDRO_EUROPEU)
        for i, num in enumerate(self.CILINDRO_EUROPEU):
            vizinhos[num] = {
                "v-2": self.CILINDRO_EUROPEU[(i - 2 + tamanho) % tamanho],
                "v-1": self.CILINDRO_EUROPEU[(i - 1 + tamanho) % tamanho],
                "v+1": self.CILINDRO_EUROPEU[(i + 1) % tamanho],
                "v+2": self.CILINDRO_EUROPEU[(i + 2) % tamanho],
            }
        return vizinhos

    def adicionar_numero(self, numero):
        if 0 <= numero <= 36:
            self.historico.append(numero)
            if len(self.historico) > 20:
                self.historico.pop(0)

    def _get_terminais_recentes(self, quantidade):
        return [n % 10 for n in self.historico[-quantidade:]]

    def _checar_cavalos_diretos(self):
        if len(self.historico) < 2: return None
        t1, t2 = self._get_terminais_recentes(2)
        if t1 == t2: return None
        for cabeca, laterais in self.CAVALOS_TRIPLOS.items():
            if set(laterais) == {t1, t2}:
                return {
                    "analise": f"Gatilho 'Cavalos Diretos' Ativado: T{t1} e T{t2} puxando o central.",
                    "estrategia": f"Focar a aposta na região do Terminal {cabeca}."
                }
        return None

    def _checar_continuacao_cavalos(self):
        if len(self.historico) < 2: return None
        terminais_unicos = set(self._get_terminais_recentes(3))
        if len(terminais_unicos) < 2: return None
        for cabeca, laterais in self.CAVALOS_TRIPLOS.items():
            trindade = {cabeca} | set(laterais)
            if len(trindade.intersection(terminais_unicos)) == 2:
                faltante = list(trindade - terminais_unicos)[0]
                return {
                    "analise": f"Gatilho 'Continuação de Cavalos' Ativado: Grupo {{{', '.join(map(str, sorted(list(trindade))))}}} está incompleto.",
                    "estrategia": f"Focar a aposta na região do cavalo faltante: Terminal {faltante}."
                }
        return None

    def _checar_manipulacao_terminal(self):
        if len(self.historico) < 5: return None
        terminais = self._get_terminais_recentes(7)
        terminal_dominante = max(set(terminais), key=terminais.count)
        contagem = terminais.count(terminal_dominante)
        if contagem >= 4:
            if contagem >= 5:
                disfarçados_str = ", ".join(map(str, sorted(list(self.DISFARCADOS[terminal_dominante]))))
                return {
                    "analise": f"Manipulação de Terminal {terminal_dominante} (SATURADO - {contagem} repetições).",
                    "estrategia": f"Antecipar a Quebra. Focar na região dos Disfarçados: {{{disfarçados_str}}}."
                }
            else:
                cavalos = self.CAVALOS_TRIPLOS[terminal_dominante]
                return {
                    "analise": f"Manipulação de Terminal {terminal_dominante} forte.",
                    "estrategia": f"Seguir a tendência. Focar na região do Cavalo Triplo {{{terminal_dominante}, {cavalos[0]}, {cavalos[1]}}}."
                }
        return None

    def analisar(self):
        if len(self.historico) < 3:
            return {"analise": "Aguardando mais números...", "estrategia": "Nenhuma ação recomendada."}

        analises_prioritarias = [
            self._checar_cavalos_diretos,
            self._checar_continuacao_cavalos,
            self._checar_manipulacao_terminal,
        ]
        for funcao_analise in analises_prioritarias:
            resultado = funcao_analise()
            if resultado:
                return resultado

        return {"analise": "Nenhum padrão tático claro identificado.", "estrategia": "Aguardar um gatilho."}

# --- Função de login ---
def check_password():
    if st.session_state.get("password_correct", False):
        return True
    password_input = st.text_input("Digite a senha:", type="password")
    CORRECT_PASSWORD = "Noah2022****"
    if st.button("Entrar"):
        if password_input == CORRECT_PASSWORD:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    return False

# --- Interface principal ---
if not check_password():
    st.stop()

st.title("Roleta Mestre - Agente Analista")

if 'analista' not in st.session_state:
    st.session_state.analista = AnalistaRoleta()

st.header("Clique no número para adicionar ao histórico:")

# Botão 0
col_zero, col_table = st.columns([1, 12])
with col_zero:
    if st.button("0", key="num_0", use_container_width=True):
        st.session_state.analista.adicionar_numero(0)
        st.rerun()

# Números 1 a 36
numeros = [[3,6,9,12,15,18,21,24,27,30,33,36],
           [2,5,8,11,14,17,20,23,26,29,32,35],
           [1,4,7,10,13,16,19,22,25,28,31,34]]

cols = st.columns(12)
for i in range(12):
    for j in range(3):
        num = numeros[j][i]
        if cols[i].button(f"{num}", key=f"num_{num}", use_container_width=True):
            st.session_state.analista.adicionar_numero(num)
            st.rerun()

st.divider()
st.header("Análise em Tempo Real")

# Exibir histórico
historico_str = ", ".join(map(str, st.session_state.analista.historico))
st.write(f"**Tempo de Tela:** {historico_str or 'Vazio'}")

# Resultado da análise
resultado_analise = st.session_state.analista.analisar()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Diagnóstico:")
    st.info(resultado_analise['analise'])
with col2:
    st.subheader("Estratégia Recomendada:")
    st.success(resultado_analise['estrategia'])

# Botão para limpar histórico
if st.button("Limpar Histórico"):
    st.session_state.analista.historico = []
    st.rerun()

# --- Gráfico de frequência ---
if st.session_state.analista.historico:
    freq = pd.Series(st.session_state.analista.historico).value_counts().sort_index()
    max_freq = freq.max()
    cores = ['red' if v == max_freq else 'orange' for v in freq.values]

    fig = px.bar(
        x=freq.index,
        y=freq.values,
        text=freq.values,
        labels={'x':'Número', 'y':'Frequência'},
        title="📊 Frequência dos Últimos Números"
    )
    fig.update_traces(
        marker_color=cores,
        marker_line_color='black',
        marker_line_width=1.5,
        textposition='outside'
    )
    st.plotly_chart(fig, use_container_width=True)

