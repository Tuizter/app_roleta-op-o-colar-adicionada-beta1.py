# app_roleta_v5_corrigido.py
import streamlit as st
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Roleta Mestre")

# --- DEFINIÇÕES DE CORES E LAYOUTS ---
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
# Ordem dos números na RODA para cálculo de vizinhos
CILINDRO_EUROPEU = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
# Ordem dos números na PISTA DE APOSTAS para visualização
LAYOUT_PISTA = {
    "curva_esquerda": [5, 10, 23, 8],
    "reta_superior": [24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35],
    "reta_inferior": [30, 11, 36, 13, 27, 6, 34, 17, 25, 2, 21, 4, 19, 15, 32],
    "curva_direita": [3, 26, 0]
}

# --- CLASSE ANALISTAROLETA ---
class AnalistaRoleta:
    def __init__(self):
        self.historico = []
        self.rodada = 0
        self.CILINDRO_EUROPEU = CILINDRO_EUROPEU
        self.VIZINHOS = self._calcular_vizinhos()
        self.CAVALOS_TRIPLOS = {0: [3, 7], 1: [4, 8], 2: [5, 9], 3: [6, 0], 4: [7, 1], 5: [8, 2], 6: [9, 3], 7: [0, 4], 8: [1, 5], 9: [2, 6]}
        self.DISFARCADOS = {0: {11, 19, 22, 28, 33}, 1: {12, 23, 29, 32, 34}, 2: {11, 13, 24, 31, 35}, 3: {12, 14, 21, 25, 26, 36}, 4: {13, 15, 22, 26, 28, 31}, 5: {14, 16, 23, 27, 32}, 6: {15, 17, 24, 28, 33}, 7: {16, 18, 25, 29, 34}, 8: {17, 19, 24, 26, 35}, 9: {18, 27, 33, 36}}

    def _calcular_vizinhos(self):
        vizinhos, tamanho = {}, len(self.CILINDRO_EUROPEU)
        for i, num in enumerate(self.CILINDRO_EUROPEU):
            vizinhos[num] = {
                "v-2": self.CILINDRO_EUROPEU[(i - 2 + tamanho) % tamanho], "v-1": self.CILINDRO_EUROPEU[(i - 1 + tamanho) % tamanho],
                "v+1": self.CILINDRO_EUROPEU[(i + 1) % tamanho], "v+2": self.CILINDRO_EUROPEU[(i + 2) % tamanho],
            }
        return vizinhos

    def _expandir_com_vizinhos(self, numeros_base):
        expandidos = set(numeros_base)
        for num in numeros_base:
            if num in self.VIZINHOS: expandidos.update(self.VIZINHOS[num].values())
        return expandidos

    def adicionar_numero(self, numero):
        if 0 <= numero <= 36:
            self.rodada += 1; self.historico.append(numero)
            if len(self.historico) > 20: self.historico.pop(0)

    def remover_ultimo(self):
        if self.historico: return self.historico.pop()
        return None

    def limpar_tudo(self):
        self.historico, self.rodada = [], 0
    
    def get_estatisticas(self):
        if not self.historico: return {'vermelho': 0, 'preto': 0, 'zero': 0, 'par': 0, 'impar': 0, 'terminais': {i: 0 for i in range(10)}}
        return {
            'vermelho': sum(1 for n in self.historico if n in CORES_NUMEROS['vermelho']), 'preto': sum(1 for n in self.historico if n in CORES_NUMEROS['preto']),
            'zero': self.historico.count(0), 'par': sum(1 for n in self.historico if n != 0 and n % 2 == 0),
            'impar': sum(1 for n in self.historico if n != 0 and n % 2 != 0), 'terminais': {i: [n % 10 for n in self.historico].count(i) for i in range(10)}
        }

    def _get_terminais_recentes(self, q): return [n % 10 for n in self.historico[-q:]]
    
    def _checar_cavalos_diretos(self):
        if len(self.historico) < 2: return None
        t1, t2 = self._get_terminais_recentes(2)
        if t1 == t2: return None
        for cabeca, laterais in self.CAVALOS_TRIPLOS.items():
            if set(laterais) == {t1, t2}:
                numeros_base = {n for n in range(37) if n % 10 == cabeca}
                return {"estrategia": f"Apostar no Terminal {cabeca} e seus vizinhos.", "numeros_alvo": self._expandir_com_vizinhos(numeros_base)}
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
                return {"estrategia": f"Apostar no Terminal faltante {faltante} e vizinhos.", "numeros_alvo": self._expandir_com_vizinhos(numeros_base)}
        return None

    def _checar_manipulacao_terminal(self):
        if len(self.historico) < 5: return None
        terminais = self._get_terminais_recentes(7)
        dom = max(set(terminais), key=terminais.count)
        contagem = terminais.count(dom)
        if contagem >= 4:
            if contagem >= 5:
                numeros_base = self.DISFARCADOS[dom]
                return {"estrategia": f"Quebra de T{dom} ({contagem}x). Apostar em Disfarçados e vizinhos.", "numeros_alvo": self._expandir_com_vizinhos(numeros_base)}
            else:
                alvo_terminais = {dom} | set(self.CAVALOS_TRIPLOS[dom])
                numeros_base = {n for n in range(37) if n % 10 in alvo_terminais}
                return {"estrategia": f"Tendência de T{dom} ({contagem}x). Apostar no Cavalo Triplo e vizinhos.", "numeros_alvo": self._expandir_com_vizinhos(numeros_base)}
        return None

    def executar_analise_completa(self):
        for funcao_analise in [self._checar_cavalos_diretos, self._checar_continuacao_cavalos, self._checar_manipulacao_terminal]:
            resultado = funcao_analise()
            if resultado: return resultado
        return {"estrategia": "Aguardar um gatilho.", "numeros_alvo": set()}

# --- FUNÇÕES DA INTERFACE (UI) ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.title("Roleta Mestre - Login")
    pwd = st.text_input("Senha:", type="password")
    if st.button("Entrar"):
        if pwd == "Noah2022****": # MUDE SUA SENHA AQUI
            st.session_state["password_correct"] = True; st.rerun()
        else: st.error("Senha incorreta.")
    return False

def get_style_caixa(num, numeros_a_destacar):
    cor_fundo = "#D22F27" if num in CORES_NUMEROS['vermelho'] else "#231F20" if num in CORES_NUMEROS['preto'] else "#006A4E"
    borda = "4px solid #FFD700" if num in numeros_a_destacar else f"2px solid {cor_fundo}"
    return f'background-color: {cor_fundo}; color: white; border: {borda};'

def gerar_tabela_visual(numeros_a_destacar):
    style_base = 'width: 60px; height: 40px; text-align: center; font-weight: bold; font-size: 16px;'
    html = "<div style='display: flex; align-items: flex-start; margin-top: 20px;'>"
    html += f"<div><table style='border-collapse: collapse;'><tr><td style='{get_style_caixa(0, numeros_a_destacar)}{style_base} height: 128px;'>0</td></tr></table></div>"
    html += "<div><table style='border-collapse: collapse;'>"
    for linha in LAYOUT_MESA:
        html += "<tr>" + "".join(f"<td style='{get_style_caixa(num, numeros_a_destacar)}{style_base}'>{num}</td>" for num in linha) + "</tr>"
    html += "</table></div></div>"
    return html

def gerar_pista_de_apostas(numeros_a_destacar):
    caixa_style = "width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white;"
    html = f"""
    <div style="width: 860px; height: 160px; background-color: #2E003E; border: 2px solid grey; border-radius: 80px; margin: 30px auto; display: flex; align-items: center; justify-content: space-between; padding: 0 10px; position: relative;">
        <!-- Curva Esquerda -->
        <div style="display: flex; flex-direction: column; justify-content: space-around; height: 100%;">
            {''.join(f'<div style="{get_style_caixa(n, numeros_a_destacar)}{caixa_style} border-radius: 15px 0 0 15px;">{n}</div>' for n in LAYOUT_PISTA["curva_esquerda"])}
        </div>
        <!-- Seção Central (Retas) -->
        <div style="display: flex; flex-direction: column; width: 100%; height: 100%; justify-content: space-between; padding: 10px 0;">
            <div style="display: flex; justify-content: center;">{''.join(f'<div style="{get_style_caixa(n, numeros_a_destacar)}{caixa_style}">{n}</div>' for n in LAYOUT_PISTA["reta_superior"])}</div>
            <div style="display: flex; justify-content: center;">{''.join(f'<div style="{get_style_caixa(n, numeros_a_destacar)}{caixa_style}">{n}</div>' for n in LAYOUT_PISTA["reta_inferior"])}</div>
        </div>
        <!-- Curva Direita -->
        <div style="display: flex; flex-direction: column; justify-content: space-around; height: 100%;">
            {''.join(f'<div style="{get_style_caixa(n, numeros_a_destacar)}{caixa_style} border-radius: 0 15px 15px 0;">{n}</div>' for n in LAYOUT_PISTA["curva_direita"])}
        </div>
        <!-- Labels Internos -->
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 90%; height: 50px; border: 1px solid #777; border-radius: 40px; display: flex; align-items: center; justify-content: space-around; color: #ccc; font-size: 14px; font-weight: bold;">
            <span style="flex: 1.2; text-align: center;">TIER</span>
            <span style="border-left: 1px solid #777; height: 100%;"></span>
            <span style="flex: 1; text-align: center;">ORPHELINS</span>
            <span style="border-left: 1px solid #777; height: 100%;"></span>
            <span style="flex: 1; text-align: center;">VOISINS</span>
            <span style="border-left: 1px solid #777; height: 100%;"></span>
            <span style="flex: 0.8; text-align: center;">ZERO</span>
        </div>
    </div>
    """
    return html

# --- INTERFACE PRINCIPAL DO APLICATIVO ---
if not check_password(): st.stop()

st.title("Roleta Mestre")

if 'analista' not in st.session_state: st.session_state.analista = AnalistaRoleta()

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Ações")
    if st.button("Desfazer Última Entrada", use_container_width=True):
        if st.session_state.analista.remover_ultimo() is not None: st.toast("Último número removido.")
        st.rerun()
    if st.button("Limpar Histórico", type="primary", use_container_width=True):
        st.session_state.analista.limpar_tudo(); st.rerun()

# --- ENTRADA DE NÚMEROS ---
st.header("Entrada de Números")
tab_botoes, tab_colar = st.tabs(["🖱️ Clicar", "📋 Colar"])
with tab_botoes:
    col_zero, col_table = st.columns([1, 12])
    with col_zero:
        if st.button("0", key="num_0", use_container_width=True): st.session_state.analista.adicionar_numero(0); st.rerun()
    with col_table:
        cols = st.columns(12)
        for i in range(12):
            for j in range(3):
                num = LAYOUT_MESA[j][i]
                if cols[i].button(f"{num}", key=f"num_{num}", use_container_width=True): st.session_state.analista.adicionar_numero(num); st.rerun()
with tab_colar:
    entrada_texto = st.text_input("Cole aqui:", placeholder="Ex: 5, 17, 32, 10")
    if st.button("Adicionar Sequência"):
        if entrada_texto:
            numeros_validos = [int(v) for v in entrada_texto.replace(",", " ").split() if v.strip().isdigit() and 0 <= int(v.strip()) <= 36]
            for n in numeros_validos: st.session_state.analista.adicionar_numero(n)
            if numeros_validos: st.success(f"Números adicionados: {', '.join(map(str, numeros_validos))}"); st.rerun()
            else: st.warning("Nenhum número válido.")

# --- ÁREA DE ANÁLISE E VISUALIZAÇÃO ---
st.divider()
st.header("Análise e Alvos")
historico_str = ", ".join(map(str, st.session_state.analista.historico))
st.info(f"**Últimos Números:** {historico_str or 'Nenhum número no histórico'}")
resultado_analise = st.session_state.analista.executar_analise_completa()
st.subheader("Estratégia Recomendada:")
st.success(resultado_analise['estrategia'])

if resultado_analise['numeros_alvo']:
    alvo_str = ", ".join(map(str, sorted(list(resultado_analise['numeros_alvo']))))
    st.write(f"**Total de {len(resultado_analise['numeros_alvo'])} números para cobrir:** {alvo_str}")
    st.markdown(gerar_pista_de_apostas(resultado_analise['numeros_alvo']), unsafe_allow_html=True)
    st.markdown(gerar_tabela_visual(resultado_analise['numeros_alvo']), unsafe_allow_html=True)

# --- ÁREA DE ESTATÍSTICAS ---
with st.expander("Ver Estatísticas do Histórico"):
    stats = st.session_state.analista.get_estatisticas()
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1: st.metric("🔴 Vermelho", stats['vermelho']); st.metric("⚫ Preto", stats['preto']); st.metric("🟢 Zero", stats['zero'])
    with stat_col2: st.metric("🔢 Par", stats['par']); st.metric("🕞 Ímpar", stats['impar'])
    with stat_col3:
        st.write("**Frequência dos Terminais:**")
        df_terminais = pd.DataFrame(list(stats['terminais'].items()), columns=['Terminal', 'Contagem']).set_index('Terminal')
        st.bar_chart(df_terminais)
