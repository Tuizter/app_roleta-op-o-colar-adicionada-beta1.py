# app_roleta_v3_corrigido.py
import streamlit as st
import pandas as pd  # <-- ESTA LINHA FOI ADICIONADA PARA CORRIGIR O ERRO

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Roleta Mestre")

# --- DEFINIÇÕES DE CORES E LAYOUT ---
CORES_NUMEROS = {
    'vermelho': {3, 9, 12, 18, 21, 27, 30, 36, 5, 14, 23, 32, 1, 7, 16, 19, 25, 34},
    'preto': {6, 15, 24, 33, 2, 8, 11, 17, 20, 26, 29, 35, 4, 10, 13, 22, 28, 31},
    'verde': {0}
}
LAYOUT_MESA = [
    [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
    [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
    [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
]
CILINDRO_EUROPEU = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]

# --- CLASSE ANALISTAROLETA ATUALIZADA ---
class AnalistaRoleta:
    def __init__(self):
        self.historico = []
        self.log_gatilhos = []
        self.rodada = 0
        self.CILINDRO_EUROPEU = CILINDRO_EUROPEU
        self.VIZINHOS = self._calcular_vizinhos()
        self.CAVALOS_TRIPLOS = {
            0: [3, 7], 1: [4, 8], 2: [5, 9], 3: [6, 0], 4: [7, 1],
            5: [8, 2], 6: [9, 3], 7: [0, 4], 8: [1, 5], 9: [2, 6]
        }
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

    def _expandir_com_vizinhos(self, numeros_base):
        numeros_expandidos = set(numeros_base)
        for num in numeros_base:
            if num in self.VIZINHOS:
                for vizinho in self.VIZINHOS[num].values():
                    numeros_expandidos.add(vizinho)
        return numeros_expandidos

    def adicionar_numero(self, numero):
        if 0 <= numero <= 36:
            self.rodada += 1
            self.historico.append(numero)
            if len(self.historico) > 20: self.historico.pop(0)
            
            resultado_analise = self.executar_analise_completa()
            if "Gatilho" in resultado_analise['analise'] or "Manipulação" in resultado_analise['analise']:
                log_msg = f"Rodada {self.rodada}: {resultado_analise['analise']}"
                if not self.log_gatilhos or self.log_gatilhos[-1] != log_msg:
                     self.log_gatilhos.append(log_msg)

    def remover_ultimo(self):
        if self.historico: return self.historico.pop()
        return None

    def limpar_tudo(self):
        self.historico, self.log_gatilhos, self.rodada = [], [], 0
    
    def get_estatisticas(self):
        if not self.historico: return {'vermelho': 0, 'preto': 0, 'zero': 0, 'par': 0, 'impar': 0, 'terminais': {i: 0 for i in range(10)}}
        stats = {
            'vermelho': sum(1 for n in self.historico if n in CORES_NUMEROS['vermelho']),
            'preto': sum(1 for n in self.historico if n in CORES_NUMEROS['preto']),
            'zero': self.historico.count(0),
            'par': sum(1 for n in self.historico if n != 0 and n % 2 == 0),
            'impar': sum(1 for n in self.historico if n != 0 and n % 2 != 0),
            'terminais': {i: [n % 10 for n in self.historico].count(i) for i in range(10)}
        }
        return stats

    def _get_terminais_recentes(self, q): return [n % 10 for n in self.historico[-q:]]
    
    def _checar_cavalos_diretos(self):
        if len(self.historico) < 2: return None
        t1, t2 = self._get_terminais_recentes(2)
        if t1 == t2: return None
        for cabeca, laterais in self.CAVALOS_TRIPLOS.items():
            if set(laterais) == {t1, t2}:
                numeros_base = {n for n in range(37) if n % 10 == cabeca}
                return {
                    "analise": f"Gatilho 'Cavalos Diretos' Ativado: T{t1} e T{t2} puxam T{cabeca}.",
                    "estrategia": f"Apostar no Terminal {cabeca} e seus vizinhos no cilindro.",
                    "numeros_alvo": self._expandir_com_vizinhos(numeros_base)
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
                numeros_base = {n for n in range(37) if n % 10 == faltante}
                return {
                    "analise": f"Gatilho 'Continuação de Cavalos': Grupo {{{', '.join(map(str, sorted(list(trindade))))}}} incompleto.",
                    "estrategia": f"Apostar no Terminal faltante {faltante} e seus vizinhos.",
                    "numeros_alvo": self._expandir_com_vizinhos(numeros_base)
                }
        return None

    def _checar_manipulacao_terminal(self):
        if len(self.historico) < 5: return None
        terminais = self._get_terminais_recentes(7)
        dom = max(set(terminais), key=terminais.count)
        contagem = terminais.count(dom)
        if contagem >= 4:
            if contagem >= 5:
                numeros_base = self.DISFARCADOS[dom]
                return {
                    "analise": f"Manipulação de T{dom} (SATURADO - {contagem}x).",
                    "estrategia": f"Antecipar quebra apostando nos Disfarçados e seus vizinhos.",
                    "numeros_alvo": self._expandir_com_vizinhos(numeros_base)
                }
            else:
                alvo_terminais = {dom} | set(self.CAVALOS_TRIPLOS[dom])
                numeros_base = {n for n in range(37) if n % 10 in alvo_terminais}
                return {
                    "analise": f"Manipulação de T{dom} forte ({contagem}x).",
                    "estrategia": f"Seguir tendência. Apostar no Cavalo Triplo {{{', '.join(map(str, sorted(list(alvo_terminais))))}}} e vizinhos.",
                    "numeros_alvo": self._expandir_com_vizinhos(numeros_base)
                }
        return None

    def executar_analise_completa(self):
        if len(self.historico) < 3: return {"analise": "Aguardando mais números...", "estrategia": "Nenhuma ação recomendada.", "numeros_alvo": set()}
        
        for funcao_analise in [self._checar_cavalos_diretos, self._checar_continuacao_cavalos, self._checar_manipulacao_terminal]:
            resultado = funcao_analise()
            if resultado: return resultado
        
        return {"analise": "Nenhum padrão tático claro identificado.", "estrategia": "Aguardar um gatilho.", "numeros_alvo": set()}

# --- FUNÇÕES DA INTERFACE (UI) ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.title("Roleta Mestre - Login")
    pwd = st.text_input("Senha:", type="password")
    if st.button("Entrar"):
        if pwd == "Noah2022****": # MUDE SUA SENHA AQUI
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("Senha incorreta.")
    return False

def get_style(num, numeros_a_destacar):
    cor_fundo = "#D22F27" if num in CORES_NUMEROS['vermelho'] else "#231F20" if num in CORES_NUMEROS['preto'] else "#006A4E"
    borda = "4px solid #FFD700" if num in numeros_a_destacar else "2px solid grey"
    return f'background-color: {cor_fundo}; color: white; border: {borda};'

def gerar_tabela_visual(numeros_a_destacar):
    style_base = 'width: 60px; height: 40px; text-align: center; font-weight: bold; font-size: 16px;'
    html = "<div style='display: flex; align-items: flex-start;'>"
    html += f"<div><table style='border-collapse: collapse;'><tr><td style='{get_style(0, numeros_a_destacar)}{style_base} height: 128px;'>0</td></tr></table></div>"
    html += "<div><table style='border-collapse: collapse;'>"
    for linha in LAYOUT_MESA:
        html += "<tr>" + "".join(f"<td style='{get_style(num, numeros_a_destacar)}{style_base}'>{num}</td>" for num in linha) + "</tr>"
    html += "</table></div></div>"
    return html

def gerar_cilindro_visual(numeros_a_destacar):
    style_base = 'width: 35px; height: 35px; display: flex; align-items: center; justify-content: center; font-weight: bold; margin: 2px; border-radius: 5px;'
    html = "<div style='display: flex; flex-wrap: wrap; justify-content: center; max-width: 800px; margin: auto;'>"
    html += "".join(f"<div style='{get_style(num, numeros_a_destacar)}{style_base}'>{num}</div>" for num in CILINDRO_EUROPEU)
    html += "</div>"
    return html

# --- INTERFACE PRINCIPAL DO APLICATIVO ---
if not check_password(): st.stop()

st.title("Roleta Mestre - Agente Analista")

if 'analista' not in st.session_state: st.session_state.analista = AnalistaRoleta()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Ações")
    if st.button("Desfazer Última Entrada", use_container_width=True):
        if st.session_state.analista.remover_ultimo() is not None: st.toast("Último número removido.")
        st.rerun()
    if st.button("Limpar Histórico", type="primary", use_container_width=True):
        st.session_state.analista.limpar_tudo()
        st.rerun()
    
    st.divider()
    st.header("Log de Gatilhos")
    if not st.session_state.analista.log_gatilhos: st.write("Nenhum gatilho ativado.")
    else: st.text_area("Histórico:", value="\n".join(st.session_state.analista.log_gatilhos[::-1]), height=300, disabled=True)

# --- ÁREA DE ENTRADA DE NÚMEROS ---
st.header("Entrada de Números")
tab_botoes, tab_colar = st.tabs(["🖱️ Clicar", "📋 Colar"])

with tab_botoes:
    col_zero, col_table = st.columns([1, 12])
    with col_zero:
        if st.button("0", key="num_0", use_container_width=True):
            st.session_state.analista.adicionar_numero(0)
            st.rerun()
    with col_table:
        cols = st.columns(12)
        for i in range(12):
            for j in range(3):
                num = LAYOUT_MESA[j][i]
                if cols[i].button(f"{num}", key=f"num_{num}", use_container_width=True):
                    st.session_state.analista.adicionar_numero(num)
                    st.rerun()

with tab_colar:
    entrada_texto = st.text_input("Cole aqui:", placeholder="Ex: 5, 17, 32, 10")
    if st.button("Adicionar Sequência"):
        if entrada_texto:
            numeros_validos = [int(v) for v in entrada_texto.replace(",", " ").split() if v.strip().isdigit() and 0 <= int(v.strip()) <= 36]
            for n in numeros_validos: st.session_state.analista.adicionar_numero(n)
            if numeros_validos:
                st.success(f"Números adicionados: {', '.join(map(str, numeros_validos))}")
                st.rerun()
            else: st.warning("Nenhum número válido encontrado.")

# --- ÁREA DE ANÁLISE ---
st.divider()
st.header("Análise em Tempo Real")

historico_str = ", ".join(map(str, st.session_state.analista.historico))
st.info(f"**Últimos Números:** {historico_str or 'Nenhum número no histórico'}")

resultado_analise = st.session_state.analista.executar_analise_completa()

col_diag, col_est = st.columns(2)
with col_diag: st.subheader("Diagnóstico:"); st.info(resultado_analise['analise'])
with col_est: st.subheader("Estratégia Recomendada:"); st.success(resultado_analise['estrategia'])

# --- ÁREA DE VISUALIZAÇÃO ---
if resultado_analise['numeros_alvo']:
    st.subheader("Visualização dos Alvos")
    alvo_str = ", ".join(map(str, sorted(list(resultado_analise['numeros_alvo']))))
    st.write(f"**Total de {len(resultado_analise['numeros_alvo'])} números para cobrir:** {alvo_str}")

    vis_col1, vis_col2 = st.columns([0.6, 0.4])
    with vis_col1:
        st.markdown("##### Destaques no Cilindro")
        st.markdown(gerar_cilindro_visual(resultado_analise['numeros_alvo']), unsafe_allow_html=True)
    with vis_col2:
        st.markdown("##### Destaques na Tabela")
        st.markdown(gerar_tabela_visual(resultado_analise['numeros_alvo']), unsafe_allow_html=True)

# --- ÁREA DE ESTATÍSTICAS ---
with st.expander("Ver Estatísticas do Histórico"):
    stats = st.session_state.analista.get_estatisticas()
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1:
        st.metric("🔴 Vermelho", stats['vermelho']); st.metric("⚫ Preto", stats['preto']); st.metric("🟢 Zero", stats['zero'])
    with stat_col2:
        st.metric("🔢 Par", stats['par']); st.metric("🕞 Ímpar", stats['impar'])
    with stat_col3:
        st.write("**Frequência dos Terminais:**")
        # Prepara o DataFrame para o gráfico
        df_terminais = pd.DataFrame(list(stats['terminais'].items()), columns=['Terminal', 'Contagem']).set_index('Terminal')
        st.bar_chart(df_terminais)
