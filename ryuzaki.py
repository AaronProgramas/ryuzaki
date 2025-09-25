import streamlit as st
import math
import random
from datetime import datetime
from html import escape
import pandas as pd
import numpy as np
# ---------------------------
# Configuração da página
# ---------------------------
st.set_page_config(page_title="Ficha Ryuzaki Kamo", layout="wide")

st.markdown("""
<style>
.big-num{font-size:2.4rem;font-weight:800;line-height:1;margin:.15rem 0 .35rem 0}
.pill{display:inline-block;padding:.15rem .55rem;border:1px solid rgba(255,255,255,.18);
      border-radius:999px;margin:.15rem .25rem 0 0;background:rgba(255,255,255,.04)}
.die{display:inline-block;font-weight:700;padding:.15rem .45rem;border-radius:.5rem;
     border:1px dashed rgba(255,255,255,.18);margin:.15rem .2rem 0 0}
.sec-label{opacity:.8;font-size:.9rem;margin-top:.25rem}
</style>
""", unsafe_allow_html=True)

def rolar_pericia(nome: str, total: int) -> dict:
    """Rola 1d20 + total para teste de perícia."""
    d20 = random.randint(1, 20)
    return {
        "Habilidade": f"Perícia – {nome}",
        "Rolagens": [d20],            # mostra o d20
        "Ataque": d20 + int(total),   # 'show_result' exibe como Ataque/Teste
    }

def pericias_ui(df):
    st.subheader('Tabela Perícias')

    col_pericia = "Perícia" if "Perícia" in df.columns else "Pericia"

    # divide o df igualmente em 2 blocos
    n = len(df)
    mid = (n + 1) // 2
    bloco_esq = df.iloc[:mid].reset_index(drop=True)
    bloco_dir = df.iloc[mid:].reset_index(drop=True)

    col_esq, col_dir = st.columns(2, gap="large")

    def render_bloco(container, bloco_df, bloco_tag):
        with container:
            # Cabeçalho visual
            h1, h2, h3 = st.columns([3, 2, 1])
            h1.markdown("**Perícia**")
            h2.markdown("**Atributo**")
            h3.markdown("**Total**")

            # Linhas com botão no Total
            for i, row in bloco_df[[col_pericia, "Atributo", "Total"]].iterrows():
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(row[col_pericia])
                c2.write(row["Atributo"])
                key = f"roll_skill_{bloco_tag}_{i}_{row[col_pericia]}"
                if c3.button(str(row["Total"]), key=key, use_container_width=True):
                    st.session_state["skill_last_output"] = (
                        f"Perícia: {row[col_pericia]}",
                        rolar_pericia(row[col_pericia], int(row["Total"]))
                    )

    render_bloco(col_esq, bloco_esq, "L")
    render_bloco(col_dir, bloco_dir, "R")



# ---------------------------
# Utilitários
# ---------------------------
def dado(faces: int, vezes: int = 1) -> list[int]:
    """Rola 'vezes' dados de 'faces' e retorna a lista com os resultados."""
    return [random.randint(1, faces) for _ in range(vezes)]

def dado_cura_aprimorada(faces: int, vezes: int = 1) -> list[int]:
    return [random.randint(3, faces) for _ in range(vezes)]

def mod(atr: int) -> int:
    """Modificador de atributo: floor((atributo-10)/2)."""
    return (atr - 10) // 2

def add_log(msg: str, payload: dict):
    """Salva o resultado no histórico da sessão."""
    if "history" not in st.session_state:
        st.session_state.history = []
    st.session_state.history.insert(0, {"msg": msg, "payload": payload, "ts": datetime.now().strftime("%H:%M:%S")})

def _pills(items):
    if not items: return ""
    html = "".join(f'<span class="pill">{escape(str(i))}</span>' for i in items)
    return f"<div>{html}</div>"

def _dice_pills(rolls):
    if not rolls: return ""
    html = "".join(f'<span class="die">{escape(str(r))}</span>' for r in rolls)
    return f"<div>{html}</div>"

def _find_numeric_by_keywords(data: dict, keywords: tuple[str, ...]):
    """Procura um valor numérico por palavra-chave no nome da chave."""
    for k, v in data.items():
        if isinstance(v, (int, float)):
            kl = k.lower()
            for kw in keywords:
                if kw in kl:
                    return k, v  # retorna a chave original e o valor
    return None, None

def show_result(title: str, data: dict):
    """Render amigável: decide o 'Resultado' de forma robusta."""
    # 1) tenta pegar "dano"/"cura" em qualquer variação do nome
    key, val = _find_numeric_by_keywords(data, ("dano", "cura"))

    if key is not None:
        primary_label = "Dano" if "dano" in key.lower() else "Cura"
        primary_value = val
    else:
        # 2) fallback: soma rolagens + mods/bônus numéricos, se existirem
        rolls = data.get("Rolagens") or data.get("rolagens") or []
        total = sum(r for r in rolls if isinstance(r, (int, float)))

        # procura campos numéricos que sejam modificadores/bônus
        bonus = 0
        for k, v in data.items():
            if isinstance(v, (int, float)):
                kl = k.lower()
                if "mod" in kl or "bônus" in kl or "bonus" in kl:
                    bonus += v

        if rolls:
            primary_label = "Resultado"
            primary_value = total + bonus
        else:
            # 3) último recurso: mostra ataque/CD ou "-"
            primary_label = "Resultado"
            primary_value = (
                data.get("Rolagem Acerto")
                or data.get("Ataque")
                or data.get("Acerto")
                or data.get("Rolagem de Ataque")
                or data.get("CD")
                or "-"
            )

    alcance = data.get("Alcance") or data.get("alcance")
    efeito  = data.get("Efeito") or data.get("efeito")
    rolls   = data.get("Rolagens") or data.get("rolagens") or []

    with st.container(border=True):
        st.markdown(f"### {title}")


        descricao = (
            data.get("Descrição") or data.get("Descricao") or
            data.get("descrição") or data.get("descricao")
        )
        if descricao:
            st.markdown(f"<p style='opacity:.85'>{escape(str(descricao))}</p>", unsafe_allow_html=True)

        left, right = st.columns([2, 1])

        with left:
            st.markdown(f'<div class="sec-label">{escape(primary_label)}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="big-num">{escape(str(primary_value))}</div>', unsafe_allow_html=True)

            if rolls:
                st.caption("Rolagens")
                st.markdown(_dice_pills(rolls), unsafe_allow_html=True)

            chips = []
            if alcance: chips.append(f"Alcance: {alcance}")
            if efeito:  chips.append(f"Efeito: {efeito}")
            if chips:
                st.markdown(_pills(chips), unsafe_allow_html=True)

        with right:
            atk_total = data.get("Rolagem de Ataque") or data.get("Ataque") or data.get("Acerto")
            cd_tr     = data.get("CD do TR") or data.get("CD")
            if atk_total is not None:
                st.metric("Rolagem Total", atk_total)
            if cd_tr is not None:
                st.metric("CD do TR", cd_tr)

    add_log(title, data)

# ---------------------------
# FICHA (base do usuário)
# ---------------------------
nivel = 6

# Atributos
For = 10
Des = 16
Con = 14
Int = 20
Sab = 13
Car = 12

# Derivados
PV = 61
PE = (6*nivel+mod(Int))+1          # Pontos de energia
maestria = math.ceil(1 + nivel/4)  # Maestria
CA_Natural, Uniforme, Escudo, Outros = 10, 4, 0, 0
CA = CA_Natural + Uniforme + Escudo + Outros + mod(Des) + mod(Int)
cd_do_tr = 10 + maestria + mod(Int) + 1

# ---------------------------
# Habilidades (coringas)
# ---------------------------

def cast_convergencia():
	rols = dado(8, 3)
	return {
	"Habilidade": "Convergência, 血を流す",
    "Custo": 1,
	"Alcance": "12m",
	"CD do TR": cd_do_tr,
    "Descrição": "Converge legal",
	"Rolagens": rols,
	"Dano (3d8)": sum(rols)+mod(Int),
	}

def cast_sangue_perfurante():
	rols = dado(8, 8)
	acerto = dado(20)[0]+feiticaria
	crit_threshold = 20+feiticaria
	crit_rols = dado(8,16)
	if acerto >= crit_threshold:
		return {
		"Habilidade": "Sangue Perfurante",
        "Custo": 4,
		"Alcance": "18m",
        "Descrição": "Perfura com sangue mt potente",
		"Rolagem de Ataque": str(acerto)+"(CRIT)",
		"Rolagens": crit_rols,
		"Dano (16d8)": sum(crit_rols)+mod(Int),
		}
	else:
		return {
		"Habilidade": "Sangue Perfurante",
        "Custo": 4,
		"Alcance": "18m",
        "Descrição": "Perfura com sangue",
		"Rolagem de Ataque": acerto,
		"Rolagens": rols,
		"Dano (8d8)": sum(rols)+mod(Int),
		}
    
def cast_poca_de_sangue():
	rols = dado(8, 7)
	rodadas = dado(2)[0]+1
	return {
	"Habilidade": "Byakuren, Chi Damari",
    "Custo": 4,
	"Alcance": "18m",
	"CD do TR": cd_do_tr,
    "Descrição": "Cria uma poça de sangue que dura "+ str(rodadas)+" rodadas",
	"Rolagens": rols,
	"Dano (3d8)": sum(rols)+mod(Int),
	}

def cast_poca_de_sangue_permanencia():
	rols = dado(12, 4)
	return {
	"Habilidade": "Byakuren, Chi Damari",
	"Alcance": "Um quadrado (1,5m)",
	"CD do TR": cd_do_tr,
    "Descrição": "Com a poça de sangue ainda no chão, tu vai tomando",
	"Rolagens": rols,
	"Dano (4d12)": sum(rols)+mod(Int),
	}

def cast_turbilhao_de_sangue():
	rols = dado(8, 3)
	return {
	"Habilidade": "Turbilhão de Sangue",
	"Alcance": "6m, raio 3m",
	"CD do TR": cd_do_tr,
    "Descrição": "Liga o liquidificador",
	"Rolagens": rols,
	"Dano (7d8)": sum(rols)+mod(Int),
	}

def cast_sangramento():
	rols = dado(8, 2)
	return {
	"Habilidade": "Sangramento - Turbilhão",
	#"Alcance": "-",
	"CD do TR": cd_do_tr,
    "Descrição": "Sangra legal até passar no teste",
	"Rolagens": rols,
	"Dano (7d8)": sum(rols)+mod(Int),
	}


# Perícias - ETL

df = pd.read_csv('pericias.csv')

# Perícias com Maestria
per_com_maestria = ['Pontaria','Reflexos', 'Fortitude', 'Integridade','Percepção', 'Ocultismo', 'Vontade','Feitiçaria','Investigação','Ofício (Alquimía)','Ofício (Culinária)']
per_com_especializacao = ['Feitiçaria', 'Investigação', 'Ofício (Culinária)']
per_outros1 = 1
per_outros2 = 2
per_com_outros1 = ['Ocultismo']
per_com_outros2 = ['Feitiçaria', 'Ofício (Culinária)']


# 1) mapa tolerante de rótulos de atributo -> modificador
attr_mod_map = {
    "for": mod(For), "força": mod(For), "forca": mod(For), "str": mod(For),
    "des": mod(Des), "dex": mod(Des), "destreza": mod(Des),
    "con": mod(Con), "constituição": mod(Con), "constituicao": mod(Con),
    "int": mod(Int), "inteligência": mod(Int), "inteligencia": mod(Int),
    "sab": mod(Sab), "sabedoria": mod(Sab),
    "car": mod(Car), "carisma": mod(Car),
}

# 2) normaliza nomes de colunas (com ou sem acento)
col_pericia = "Pericia" if "Pericia" in df.columns else "Pericia"

# 3) componentes
df["ModAtrib"] = df["Atributo"].map(lambda s: attr_mod_map.get(str(s).strip().lower(), 0))
df["LvlHalf"]  = nivel // 2
df["Maestria"] = np.where(df[col_pericia].isin(per_com_maestria), maestria, 0)
df['Especializacao'] = np.where(df[col_pericia].isin(per_com_especializacao), maestria, 0)
df["Outros1"]   = np.where(df[col_pericia].isin(per_com_outros1), per_outros1, 0)
df["Outros2"]   = np.where(df[col_pericia].isin(per_com_outros2), per_outros2, 0)

# 4) total final
df["Total"] = df["ModAtrib"] + df["LvlHalf"] + df["Maestria"] + df['Especializacao'] + df["Outros1"] + df["Outros2"]

# Perícia da porrada
feiticaria = int(df.loc[df["Pericia"] == "Feitiçaria", "Total"].values[0])


# ---------------------------
# LAYOUT
# ---------------------------
#st.title("Ficha - Ryuzaki Kamo")

# ----- Colunas principais
col_ficha, col_pericias, col_habs = st.columns([2, 3, 2], gap="large")

st.sidebar.title('Ryuzaki Kamo')
st.sidebar.image('Ryuzaki.png')
st.sidebar.subheader('Quem é O Homem?')
st.sidebar.write('Ryuzaki Kamo, do clã Kamo, é uma unidade absoluta da manipulação de sangue, sendo capaz de usar sua técnica para explodir qualquer tralha que ouse enfrentar a tropa.')
st.sidebar.write('')
st.sidebar.write('É considerado por muitos o futuro presidente Jujutsu, aquele que irá macetar a oposição.')


# ----- Col Pericias
with col_pericias:
    pericias_ui(df)

# ----- Coluna Ficha (sidebar visual)
with col_ficha:
    st.subheader("📜 Ficha do Personagem")
    with st.container(border=True):
        st.markdown("#### Nível e Recursos")
        c1, c2, c3 = st.columns(3)
        c1.metric("Nível", nivel)
        c2.metric(f"Maestria", maestria)
        c3.metric("Atenção", 10+((nivel//2)+mod(Sab)))
        c1.metric("PV", PV)
        c2.metric("PE", PE)
        c3.metric("CA", CA)

        # estado inicial (iguais ao máximo)
        if "pv_atual" not in st.session_state:
            st.session_state.pv_atual = PV
        if "pe_atual" not in st.session_state:
            st.session_state.pe_atual = PE

        # uma única linha com inputs, alinhados com PV/PE
        c1.number_input("PV atual", min_value=0, max_value=PV, step=1, key="pv_atual")
        c2.number_input("PE atual", min_value=0, max_value=PE, step=1, key="pe_atual")


        st.markdown("---")
        st.markdown("#### Atributos")
        a1, a2 = st.columns(2)
        a1.write(f"**For**: {For} ({mod(For):+d})")
        a1.write(f"**Des**: {Des} ({mod(Des):+d})")
        a1.write(f"**Con**: {Con} ({mod(Con):+d})")
        a2.write(f"**Int**: {Int} ({mod(Int):+d})")
        a2.write(f"**Sab**: {Sab} ({mod(Sab):+d})")
        a2.write(f"**Car**: {Car} ({mod(Car):+d})")
        st.markdown("### 🧾 Histórico")
    
    if "history" in st.session_state and st.session_state.history:
        for item in st.session_state.history[:10]:
            with st.expander(f"[{item['ts']}] {item['msg']}", expanded=False):
                st.json(item["payload"], expanded=False)
    else:
        st.caption("Sem rolagens ainda. Lance uma habilidade!")

# ----- Coluna Habilidades
with col_habs:
    st.subheader("Habilidades")

    # --- botões (apenas definem o 'clicked')
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    c5, c6 = st.columns(2)

    clicked = None
    if c1.button("🩸 Convergência, 血を流す", use_container_width=True):
        clicked = ("Convergência, 血を流す", cast_convergencia())
    if c2.button("🩸 Sangue Perfurante", use_container_width=True):
        clicked = ("Sangue Perfurante", cast_sangue_perfurante())
    if c3.button("🩸 Poça de Sangue", use_container_width=True):
        clicked = ("Poça de Sangue", cast_poca_de_sangue())
    if c4.button("🩸 Poça de Sangue - Permanencia", use_container_width=True):
        clicked = ("Poça de Sangue - Permanencia", cast_poca_de_sangue_permanencia())
    if c5.button("🩸 Turbilhão de Sangue", use_container_width=True):
        clicked = ("Turbilhão de Sangue", cast_turbilhao_de_sangue())
    if c6.button("🩸 Sangramento", use_container_width=True):
        clicked = ("Turbilhão de Sangue - Sangramento", cast_sangramento())

    # salva o último output clicado
    if clicked:
        st.session_state["last_output"] = clicked

    st.markdown("---")

    # --- render fixo do output (sempre abaixo do '---')
    if "last_output" in st.session_state:
        title, payload = st.session_state["last_output"]
        show_result(title, payload)
    else:
        st.caption("Clique numa habilidade para rolar.")

    st.markdown("---")

    st.subheader("Perícias")
    # Resultado fixo acima da tabela
    if "skill_last_output" in st.session_state:
        title, payload = st.session_state["skill_last_output"]
        show_result(title, payload)
    else:
        st.caption("Clique no valor Total para rolar a perícia.")