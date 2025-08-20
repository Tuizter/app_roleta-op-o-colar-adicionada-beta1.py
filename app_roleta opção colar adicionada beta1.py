# app_roleta_v2.py
import streamlit as st
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
# DEVE SER O PRIMEIRO COMANDO DO STREAMLIT NO CÓDIGO
st.set_page_config(layout="wide", page_title="Roleta Mestre")


# --- DEFINIÇÕES DE CORES E LAYOUT ---
# Usado para as estatísticas e para a tabela visual
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

# --- CLASSE ANALISTAROLETA ATUALIZADA ---
class AnalistaRoleta:
    def __init__(self):
        self.historico = []
        self.log_gatilhos = []
        self.rodada = 0
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
            self.rodada += 1
            self.historico.append(numero)
            if len(self.historico) > 20:
                self.historico.pop(0)
            
            resultado_analise = self._executar_analise_completa()
            if "Gatilho" in resultado_analise['analise'] or "Manipulação" in resultado_analise['analise']:
                if not self.log_gatilhos or self.log_gatilhos[-1] != f"Rodada {self.rodada}: {resultado_analise['analise']}":
                     self.log_gatilhos.append(f"Rodada {self.rodada}: {resultado_analise['analise']}")

    def remover_ultimo(self):
        if self.historico:
            return self.historico.pop()
        return None

    def limpar_tudo(self):
        self.historico = []
        self.log_gatilhos = []
        self.rodada = 0
    
    def get_estatisticas(self):
        if not self.historico:
            return {'vermelho': 0, 'preto': 0, 'zero': 0, 'par': 0, 'impar': 0, 'terminais': {i: 0 for i in range(10)}}
        
        vermelho = sum(1 for n in self.historico if n in CORES_NUMEROS['vermelho'])
        preto = sum(1 for n in self.historico if n in CORES_NUMEROS['preto'])
        zero = self.historico.count(0)
        par = sum(1 for n in self.historico if n != 0 and n % 2 == 0)
        impar = sum(1 for n in self.historico if n != 0 and n % 2 != 0)
        terminais_hist = [n % 10 for n in self.historico]
        terminais_contagem = {i: terminais_hist.count(i) for i in range(10)}
        
        return {'vermelho': vermelho, 'preto': preto, 'zero': zero, 'par': par, 'impar': impar, 'terminais': terminais_contagem}

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
                    "estrategia": f"Focar a aposta na região do Terminal {cabeca}.",
                    "numeros_alvo": {n for n in range(37) if n % 10 == cabeca}
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
                    "estrategia": f"Focar a aposta na região do cavalo faltante: Terminal {faltante}.",
                    "numeros_alvo": {n for n in range(37) if n % 10 == faltante}
                }
        return None

    def _checar_manipulacao_terminal(self):
        if len(self.historico) < 5: return None
        terminais = self._get_terminais_recentes(7)
        terminal_dominante = max(set(terminais), key=terminais.count)
        contagem = terminais.count(terminal_dominante)
        if contagem >= 4:
            if contagem >= 5:
                disfarçados = self.DISFARCADOS[terminal_dominante]
                disfarçados_str = ", ".join(map(str, sorted(list(disfarçados))))
                return {
                    "analise": f"Manipulação de Terminal {terminal_dominante} (SATURADO - {contagem} repetições).",
                    "estrategia": f"Antecipar a Quebra. Focar na região dos Disfarçados: {{{disfarçados_str}}}.",
                    "numeros_alvo": disfarçados
                }
            else:
                cavalos = self.CAVALOS_TRIPLOS[terminal_dominante]
                alvo_terminais = {terminal_dominante, cavalos[0], cavalos[1]}
                numeros_alvo = {n for n in range(37) if n % 10 in alvo_terminais}
                return {
                    "analise": f"Manipulação de Terminal {terminal_dominante} forte.",
                    "estrategia": f"Seguir a tendência. Focar na região do Cavalo Triplo {{{terminal_dominante}, {cavalos[0]}, {cavalos[1]}}}.",
                    "numeros_alvo": numeros_alvo
                }
        return None

    def _executar_analise_completa(self):
        if len(self.historico) < 3:
            return {"analise": "Aguardando mais números...", "estrategia": "Nenhuma ação recomendada.", "numeros_alvo": set()}
        
        analises_prioritarias = [
            self._checar_cavalos_diretos,
            self._checar_continuacao_cavalos,
            self._checar_manipulacao_terminal,
        ]
        for funcao_analise in analises_prioritarias:
            resultado = funcao_analise()
            if resultado:
                return resultado
        
        return {"analise": "Nenhum padrão tático claro identificado.", "estrategia": "Aguardar um gatilho.", "numeros_alvo": set()}

# --- FUNÇÕES DA INTERFACE (UI) ---

def check_password():
    """Retorna True se o usuário tiver digitado a senha correta."""
    if st.session_state.get("password_correct", False):
        return True

    st.title("Roleta Mestre - Login")
    password_input = st.text_input("Digite a senha para acessar:", type="password", key="password_input")
    
    # MUDE SUA SENHA AQUI
    CORRECT_PASSWORD = "Noah2022****" 
    
    if st.button("Entrar"):
        if password_input == CORRECT_PASSWORD:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    return False

def gerar_tabela_visual(numeros_a_destacar):
    """Gera uma tabela HTML da roleta, destacando os números alvo."""
    
    def get_style(num):
        cor_fundo = "#D22F27" if num in CORES_NUMEROS['vermelho'] else "#231F20" if num in CORES_NUMEROS['preto'] else "#006A4E"
        cor_texto = "white"
        borda = "4px solid #FFD700" if num in numeros_a_destacar else "2px solid grey" # Destaque amarelo
        return f'background-color: {cor_fundo}; color: {cor_texto}; border: {borda}; width: 60px; height: 40px; text-align: center; font-weight: bold; font-size: 16px;'

    html = "<div style='display: flex; align-items: flex-start;'>"
    # Coluna do Zero
    html += f"<div><table style='border-collapse: collapse;'><tr><td style='{get_style(0)}; height: 128px;'>0</td></tr></table></div>"
    # Colunas principais
    html += "<div><table style='border-collapse: collapse;'>"
    for linha in LAYOUT_MESA:
        html += "<tr>"
        for num in linha:
            html += f"<td style='{get_style(num)}'>{num}</td>"
        html += "</tr>"
    html += "</table></div></div>"
    return html

# --- INTERFACE PRINCIPAL DO APLICATIVO ---

if not check_password():
    st.stop()

st.title("Roleta Mestre - Agente Analista")

# Inicializa o analista no estado da sessão
if 'analista' not in st.session_state:
    st.session_state.analista = AnalistaRoleta()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Ações e Opções")
    if st.button("Desfazer Última Entrada", use_container_width=True):
        num_removido = st.session_state.analista.remover_ultimo()
        if num_removido is not None:
            st.toast(f"Número {num_removido} removido.")
        st.rerun()

    if st.button("Limpar Histórico", type="primary", use_container_width=True):
        st.session_state.analista.limpar_tudo()
        st.rerun()
    
    st.divider()
    
    with st.expander("**Como Mudar o Tema (Claro/Escuro)**", expanded=False):
        st.info("""
        O Streamlit permite que você defina um tema criando uma pasta e um arquivo:
        1. No mesmo diretório do seu app, crie uma pasta chamada `.streamlit`.
        2. Dentro dela, crie um arquivo chamado `config.toml`.
        3. Cole o seguinte texto no arquivo para o **Tema Escuro**:
        ```toml
        [theme]
        base="dark"
        primaryColor="#FF4B4B"
        backgroundColor="#0E1117"
        secondaryBackgroundColor="#262730"
        textColor="#FAFAFA"
        ```
        Para o **Tema Claro**, use:
        ```toml
        [theme]
        base="light"
        primaryColor="#FF4B4B"
        backgroundColor="#FFFFFF"
        secondaryBackgroundColor="#F0F2F6"
        textColor="#31333F"
        ```
        Salve o arquivo e reinicie o app.
        """)

    st.header("Log de Gatilhos")
    if not st.session_state.analista.log_gatilhos:
        st.write("Nenhum gatilho ativado ainda.")
    else:
        log_invertido = st.session_state.analista.log_gatilhos[::-1] # Mostra o mais recente primeiro
        st.text_area("Histórico de Análises:", value="\n".join(log_invertido), height=300, disabled=True)


# --- ÁREA DE ENTRADA DE NÚMEROS ---
st.header("Entrada de Números")
tab_botoes, tab_colar = st.tabs(["🖱️ Clicar nos Botões", "📋 Colar Sequência"])

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
    entrada_texto = st.text_input("Cole aqui separados por vírgula ou espaço", placeholder="Ex: 5, 17, 32, 10")
    if st.button("Adicionar Sequência"):
        if entrada_texto:
            valores = entrada_texto.replace(",", " ").split()
            numeros_validos = []
            for v in valores:
                try:
                    num = int(v)
                    if 0 <= num <= 36:
                        numeros_validos.append(num)
                except:
                    pass 
            for n in numeros_validos:
                st.session_state.analista.adicionar_numero(n)
            
            if numeros_validos:
                st.success(f"Números adicionados: {', '.join(map(str, numeros_validos))}")
                st.rerun()
            else:
                st.warning("Nenhum número válido foi encontrado.")

# --- ÁREA DE ANÁLISE ---
st.divider()
st.header("Análise em Tempo Real")

historico_str = ", ".join(map(str, st.session_state.analista.historico))
st.write(f"**Últimos Números (Tempo de Tela):**")
st.info(f"**{historico_str or 'Nenhum número no histórico'}**")

resultado_analise = st.session_state.analista._executar_analise_completa()

col_diag, col_est, col_vis = st.columns([0.35, 0.35, 0.3])

with col_diag:
    st.subheader("Diagnóstico:")
    st.info(resultado_analise['analise'])

with col_est:
    st.subheader("Estratégia Recomendada:")
    st.success(resultado_analise['estrategia'])

with col_vis:
    st.subheader("Alvos Visuais:")
    if not resultado_analise['numeros_alvo']:
        st.write("Nenhum alvo específico.")
    else:
        # Mostra os números em texto
        alvo_str = ", ".join(map(str, sorted(list(resultado_analise['numeros_alvo']))))
        st.write(f"**Apostar em:** {alvo_str}")

# Adiciona a tabela visual com destaque
st.markdown(gerar_tabela_visual(resultado_analise['numeros_alvo']), unsafe_allow_html=True)


# --- ÁREA DE ESTATÍSTICAS ---
with st.expander("Ver Estatísticas do Histórico"):
    stats = st.session_state.analista.get_estatisticas()
    
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    
    with stat_col1:
        st.metric("🔴 Vermelho", stats['vermelho'])
        st.metric("⚫ Preto", stats['preto'])
        st.metric("🟢 Zero", stats['zero'])
        
    with stat_col2:
        st.metric("🔢 Par", stats['par'])
        st.metric("🕞 Ímpar", stats['impar'])
    
    with stat_col3:
        st.write("**Frequência dos Terminais:**")
        df_terminais = pd.DataFrame(list(stats['terminais'].items()), columns=['Terminal', 'Contagem']).set_index('Terminal')
        st.bar_chart(df_terminais)
