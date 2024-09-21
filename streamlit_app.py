import streamlit as st
import json
from collections import Counter
from matplotlib import pyplot as plt
from matplotlib_venn import venn2
from wordcloud import WordCloud
import re
import itertools
import operator
import math
import numpy as np
from streamlit_extras.stylable_container import stylable_container

def läsa_in_json_fil(filnamn):
    with open(filnamn) as fil:
        innehåll = fil.read()
    utdata = json.loads(innehåll)
    return utdata

def skapa_json_fil(filnamn, data_att_spara):
    with open(filnamn, "w", encoding= "utf-8") as outfile:
        json.dump(data_att_spara, outfile, ensure_ascii=False, indent = 2, separators = (", ", ": "))
        #JSON-filen innehåller följande delar
        # all_data["giltiga_yrksnamn"]
        # all_data["länskod_länsnamn"]
        # all_data["susaområden_inriktningar"]
        # all_data["yrkesid_topplista_liknande"]
        # all_data["yrkesid_topplista_skills"]
        # all_data["susaid_topplista_skills"]
        # all_data["yrkesid_område"]
        # all_data["yrkesid_ssykid"]
        # all_data["yrkesid_namn"]
        # all_data["yrkesid_topplista_taxonomibegrepp"]
        # all_data["yrkesid_länskod_annonser"]
        # all_data["yrkesid_länskod_prognos"]

def skapa_venn(indata):
    yrkestitlar = []
    skills = []
    for k, v in indata.items():
        if k:
            yrkestitlar.append(k)
        if v:
            skills.append(set(v))
    plt.figure(figsize= (12, 8))
    venn = venn2(subsets = skills, set_labels = yrkestitlar, set_colors = ["skyblue", "lightgreen"])
    try:
        venn.get_label_by_id("10").set_text("\n".join(skills[0] - skills[1]))
    except:
        pass
    try:
        venn.get_label_by_id("11").set_text("\n".join(skills[0] & skills[1]))
    except:
        pass
    try:
        venn.get_label_by_id("01").set_text("\n".join(skills[1] - skills[0]))
    except:
        pass
    return plt

def räkna_förekomster(data):
    utdata = {}
    data = Counter(data)
    for k, a in data.items():
        utdata[k] = a
    return utdata

def jämföra_bakgrund_med_liknande(indata, valda_ord):
    utdata = {}
    alla_skills = []
    unika = []
    överlappande = []
    for i in indata:
        alla_skills = alla_skills + i["skills"]
    alla_skills = räkna_förekomster(alla_skills)
    for k, v in alla_skills.items():
        if v == 1:
            unika.append(k)
    for i in indata:
        antal_unika = 0
        antal_tillagda = 0
        antal_överlappande = 0
        utdata[i["namn"]] = []
        for s in i["skills"]:
            if s in unika:
                if antal_unika < 11:
                    if s in valda_ord:
                        utdata[i["namn"]].append(f"\u00BB{s}")
                    else:
                        utdata[i["namn"]].append(s)
                    antal_tillagda += 1
                    antal_unika += 1
            else:
                if antal_överlappande < 11:
                    överlappande.append(s)
                    antal_tillagda += 1
                    antal_överlappande += 1
    for i in indata:
        for s in i["skills"]:
            if s in överlappande:
                if s in valda_ord:
                    utdata[i["namn"]].append(f"\u00BB{s}")
                else:
                    utdata[i["namn"]].append(s)
    return utdata

def skapa_liknande_yb(id_valt_yrke, intresse, data):
    alla_liknande_med_skills = {}
    alla_liknande_yb = []
    liknande_yrken = data["yrkesid_topplista_liknande"].get(id_valt_yrke)
    if intresse == "inte":
        antal_samma = 0
        antal_annat = 4
    elif intresse == "intresserad" or intresse == None:
        antal_samma = 2
        antal_annat = 2
    elif intresse == "mycket":
        antal_samma = 4
        antal_annat = 0
    antal_gjorda = 0
    while antal_gjorda < antal_samma:
        try:
            liknande_yb = liknande_yrken["liknande_samma_område"][antal_gjorda]
            liknande_namn = data["yrkesid_namn"].get(liknande_yb)
            antal_gjorda += 1
            info_liknande = data["yrkesid_topplista_skills"].get(liknande_yb)
            if info_liknande:
                alla_liknande_yb.append(liknande_namn)
                alla_liknande_med_skills[liknande_namn] = info_liknande["skills"]
        except:
            antal_gjorda += 1
    antal_gjorda = 0
    while antal_gjorda < antal_annat:
        try:
            liknande_yb = liknande_yrken["liknande_annat_område"][antal_gjorda]
            liknande_namn = data["yrkesid_namn"].get(liknande_yb)
            antal_gjorda += 1
            info_liknande = data["yrkesid_topplista_skills"].get(liknande_yb)
            if info_liknande:
                alla_liknande_yb.append(liknande_namn)
                alla_liknande_med_skills[liknande_namn] = info_liknande["skills"]
        except:
            antal_gjorda += 1
    return alla_liknande_yb, alla_liknande_med_skills

def addera_prognos_antal_annonser(liknande, data, län):
    utdata = []
    länsnummer = str(list(filter(lambda x: data["länskod_länsnamn"][x] == län, data["länskod_länsnamn"]))[0])
    for i in liknande:
        try:
            id = list(filter(lambda x: data["yrkesid_namn"][x] == i, data["yrkesid_namn"]))[0]
            try:
                prognos = data["yrkesid_länskod_prognos"].get(id)
                for p in prognos:
                    if p["län"] == länsnummer:
                        länsprognos = p["prognos"]
                if länsprognos == "små":
                    pil = "\u2193"
                elif länsprognos == "medelstora":
                    pil = "\u2192"
                elif länsprognos == "stora":
                    pil = "\u2191"
                else:
                    pil = ""
            except:
                pil = ""
            try:
                annonsantal_yrke = data["yrkesid_länskod_annonser"].get(id)
                annonsantal_sverige = 0
                for value in annonsantal_yrke.values():
                    annonsantal_sverige += value
                annonsantal_län = annonsantal_yrke.get(länsnummer)
                if not annonsantal_län:
                    annonsantal_län = 0
            except:
                annonsantal_län = 0
            utdata.append(str(f"{i}({län} {annonsantal_län}{pil}, Sverige {annonsantal_sverige})"))
        except:
            pass
    return utdata

def skapa_intresseord(skills_valt_yrke, liknande_yb):
    bakgrundsyrke_skills = list(skills_valt_yrke.keys())
    bakgrundsyrke_skills = bakgrundsyrke_skills[0:50]
    liknande_yb_skills = {}
    for value in liknande_yb.values():
        liknande_yb_skills = dict(Counter(liknande_yb_skills) + Counter(value))
    valbara_intresseord = []
    for i in liknande_yb_skills:
        if not i in bakgrundsyrke_skills:
            valbara_intresseord.append(i)
    return valbara_intresseord

def skapa_jämförelselista(namn_utgång, skills_utgång, namn_liknande, skills_liknande, valda_ord):
    utdata = []
    skills_utgång = list(skills_utgång.keys())
    for s in skills_utgång:
        if s in valda_ord:
            plats_att_flytta_från = skills_utgång.index(s)
            ord_att_flytta = skills_utgång.pop(plats_att_flytta_från)
            skills_utgång.insert(0, ord_att_flytta)
    bakgrund = {"namn": namn_utgång,
                "skills": skills_utgång}
    utdata.append(bakgrund)
    liknande_skills = list(skills_liknande.keys())
    for k in liknande_skills:
        if k in valda_ord:
            plats_att_flytta_från = liknande_skills.index(k)
            ord_att_flytta = liknande_skills.pop(plats_att_flytta_från)
            liknande_skills.insert(0, ord_att_flytta)
    liknande = {"namn": namn_liknande,
                "skills": liknande_skills}
    utdata.append(liknande)
    return utdata

def ändra_färger_på_ord(erfarenheter, intressen):
    def test_color_func(word, font_size, position, orientation, font_path, random_state):
        if word in intressen:
            return 'blue'
        elif word in erfarenheter:
            return 'green'
        else:
            r, g, b, alpha = plt.get_cmap('cividis')(font_size / 120)
            return (int(r * 255), int(g * 255), int(b * 255))
    return test_color_func

def skapa_ordmoln(skills_molnyrke, skills_bakgrund, erfarenhetsord, intresseord):
    wordcloud = WordCloud(width=800, height=800,
                          background_color= 'white',
                          prefer_horizontal=1).generate_from_frequencies(skills_molnyrke)
    vald_erfarenhet = erfarenhetsord
    beräknad_erfarenhet = list(skills_bakgrund.keys())
    erfarenhet = vald_erfarenhet + beräknad_erfarenhet
    wordcloud.recolor(color_func = ändra_färger_på_ord(erfarenhet, intresseord))
    plt.figure(figsize = (6, 6), facecolor=None)
    plt.imshow(wordcloud)
    plt.axis('off')
    plt.tight_layout(pad=0)
    return plt

def rensa_text_till_länk(text):
    text = text.strip()
    text = text.lower()
    att_rensa = {
        " ": "%20",
        "\^": "%5E",
        "'": "%22"}
    for key, value in att_rensa.items():
        text = re.sub(key, value, text)
    return text

def skapa_länk(ssyk, skills, länsid):
    grund = f"https://arbetsformedlingen.se/platsbanken/annonser?p=5:{ssyk}&q="
    splittade_skills = []
    for s in skills:
        s = rensa_text_till_länk(s)
        splittade_skills.append(s)
    splittade_skills = "%20".join(splittade_skills)
    län = "&l=2:" + länsid
    return grund + splittade_skills + län

def skapa_länk_till_platsbanken(liknande_id, liknande_skill, erfarenhetsord, intresseord, data, länsid):
    antal_skills_att_söka = 15
    ssyk = data["yrkesid_ssykid"].get(liknande_id)
    skills_som_lista = list(liknande_skill.keys())
    alla_skills = erfarenhetsord + intresseord + skills_som_lista
    alla_skills = alla_skills[0:antal_skills_att_söka]
    länk = skapa_länk(ssyk, alla_skills, länsid)
    return länk

def norma(data):
    return math.sqrt(sum(x * x for x in data.values()))

def räkna_cosine(A, B):
    nycklar_i_båda = list(A.keys() & B.keys())
    Aa = list(A[k] for k in nycklar_i_båda)
    Bb = list(B[k] for k in nycklar_i_båda)
    cosine = np.dot(Aa, Bb) / (norma(A) * norma(B))
    return round(cosine, 2)

def cosine_mellan_bakgrund_och_alla_yrken(skills_utb, intresse, data):
    alla_liknande_yb = []
    if intresse == "inte" or intresse == None:
        antal_att_spara = 4
    elif intresse == "intresserad":
        antal_att_spara = 4
    elif intresse == "mycket":
        antal_att_spara = 4
    for k, v in data["yrkesid_topplista_skills"].items():
        skills = v["skills"]
        yb = data["yrkesid_namn"].get(k)
        cosine = räkna_cosine(skills_utb, skills)
        liknande_yb = {
            "id": k,
            "namn": yb,
            "cosine": cosine,
            "skills": skills}
        alla_liknande_yb.append(liknande_yb)
    alla_liknande_yb = (sorted(alla_liknande_yb, key = operator.itemgetter("cosine"), reverse = True))
    alla_liknande_yb = list(itertools.islice(alla_liknande_yb, antal_att_spara))
    namn_liknande_yb = []
    liknande_med_skills = {}
    for i in alla_liknande_yb:
        namn_liknande_yb.append(i["namn"])
        liknande_med_skills[i["namn"]] = i["skills"]
    return namn_liknande_yb, liknande_med_skills

def välja_yrke(valt_yrke, data, länsid):
    id_valt_yrke = list(filter(lambda x: data["yrkesid_namn"][x] == valt_yrke, data["yrkesid_namn"]))[0]
    område = data["yrkesid_område"].get(id_valt_yrke)

    col1, col2 = st.columns(2)

    with col1:
        erfarenhet = st.radio(
            f"Hur mycket erfarenhet har du som {valt_yrke}?",
            ["oerfaren", "erfaren", "mycket erfaren"],
            horizontal = True, index = None,
        )

        rörlighet = st.radio(
            f"Kan du tänka dig att söka jobb i närheten av {valt_län}?",
            ["ja", "nej"],
            horizontal = True, index = None,
        )

    with col2:
        intresse = st.radio(
            f"Hur intresserad är du av yrken inom yrkesområdet {område}?",
            ["inte", "intresserad", "mycket"],
            horizontal = True, index = None,
        )

        utbildningsintresse = st.radio(
            f"Skulle du vara intresserad av en längre utbildning för att hitta ett nytt yrke?",
            ["ja", "nej"],
            horizontal = True, index = None,
        )

    antal_att_visa_upp = 20

    info_valt_yrke = data["yrkesid_topplista_skills"].get(id_valt_yrke)
    skills_valt_yrke = info_valt_yrke["skills"]
    skills = list(skills_valt_yrke.keys())
    erfarenhetsord = skills[0:antal_att_visa_upp]

    valda_erfarenhetsord = st.multiselect(
        f"Här är en lista på några ord från annonser för {valt_yrke}. Välj ett eller flera ord som beskriver vad du är bra på",
        (erfarenhetsord),)

    liknande_yb, liknande_yb_skills = skapa_liknande_yb(id_valt_yrke, intresse, data)

    liknande_yb_med_prognos = addera_prognos_antal_annonser(liknande_yb, data, valt_län)

    intresseord = skapa_intresseord(skills_valt_yrke, liknande_yb_skills)
    intresseord = intresseord[0:antal_att_visa_upp]

    valda_intresseord = st.multiselect(
        f"Här kommer en lista på några ord från annonser för yrkesbenämningar som på ett eller annat sätt liknar det du tidigare har jobbat med. Välj ett eller flera ord som beskriver vad du är intresserad av",
        (intresseord),)

    st.write("Nedan finns länkar till annonser för några liknande yrken utifrån tillhörande yrkesgrupp och valda erfarenhets- och intresseord")

    col1, col2 = st.columns(2)

    antal = 0
    for i in liknande_yb:
        try:
            id_liknande_yrke = list(filter(lambda x: data["yrkesid_namn"][x] == i, data["yrkesid_namn"]))[0]
            skills_liknande = liknande_yb_skills.get(i)
            länk = skapa_länk_till_platsbanken(id_liknande_yrke, skills_liknande, valda_erfarenhetsord, valda_intresseord, data, länsid)
            if (antal % 2) == 0:
                col1.link_button(i, länk)
            else:
                col2.link_button(i, länk)
            antal += 1
        except:
            pass

    with stylable_container(
        key= "green_button",
        css_styles = """
        button {
            display: inline-block;
            outline: none;
            cursor: pointer;
            font-size: 12px;
            line-height: 1;
            border-radius: 400px;
            transition-property: background-color,border-color,color,box-shadow,filter;
            transition-duration: .3s;
            border: 1px solid transparent;
            letter-spacing: 2px;
            min-width: 100px;
            white-space: normal;
            font-weight: 700;
            text-align: center;
            padding: 8px 20px;
            color: #fff;
            background-color: #1ED760;
            height: 20px;
            :hover{
                transform: scale(1.04);
                background-color: #21e065;
                    }
            """,
    ):
        st.button("Spara bakgrund", on_click = spara_data, args = (valt_yrke, valda_erfarenhetsord, valda_intresseord, liknande_yb))
        
    vald_liknande = st.selectbox(
        "Välj ett liknande yrke som du skulle vilja veta mer om",
        (liknande_yb_med_prognos),index = None)
    
    if vald_liknande:
        vald_liknande_split = vald_liknande.split("(")
        vald_liknande = vald_liknande_split[0]
        skills_liknande = liknande_yb_skills.get(vald_liknande)
        valda_ord = valda_erfarenhetsord + valda_intresseord
        jämförelselista = skapa_jämförelselista(valt_yrke, skills_valt_yrke, vald_liknande, skills_liknande, valda_ord)

        id_liknande_yrke = list(filter(lambda x: data["yrkesid_namn"][x] == vald_liknande, data["yrkesid_namn"]))[0]

        try:
            af_kompetenser = data["yrkesid_topplista_taxonomibegrepp"].get(id_liknande_yrke)
            if not af_kompetenser:
                af_kompetenser = ["Kunde inte hitta någon data"]
        except:
            af_kompetenser = ["Kunde inte hitta någon data"]
        taxonomi = ("  \n ").join(af_kompetenser)

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"Till höger ser du kompetenser som många arbetsgivare efterfrågar när de söker efter en {vald_liknande}")

        with col2:
            st.write(taxonomi)

        st.divider()

        st.write(f"Nedanför ser du ord som många arbetsgivare använder i annonser för {vald_liknande}")

        ordmoln = skapa_ordmoln(skills_liknande, skills_valt_yrke, valda_erfarenhetsord, valda_intresseord)
        st.pyplot(ordmoln)

        st.divider()

        st.write(f"Nedanför ser du likheter och skillnader mellan hur olika arbetsgivare och utbildningsanordnare uttrycker sig när det kommer till kunskaper, erfarenheter och arbetsuppgifter för {valt_yrke} och {vald_liknande}")

        venn_data = jämföra_bakgrund_med_liknande(jämförelselista, valda_ord)
        venn = skapa_venn(venn_data)
        st.pyplot(venn)

def välja_yrkesbakgrund(data, valt_län, länsid):
    giltiga_yb = data["giltiga_yrksnamn"]
    giltiga_yb = sorted(giltiga_yb)

    yrkesval_områdesval = st.radio(
            f"Vill du välja ett yrke direkt eller orientera dig fram från ett yrkesområde?",
            ["välja yrke", "välja yrkesområde"],
            horizontal = True, index = 0,
        )
    
    if yrkesval_områdesval == "välja yrke":
        valt_yrke = st.selectbox(
            "Välj ett yrke som du tidigare har arbetat som",
            (giltiga_yb), placeholder = "välj", index = None)

        if valt_yrke:
            välja_yrke(valt_yrke, data, länsid)
    
    elif yrkesval_områdesval == "välja yrkesområde":

        områdes_ssyk_yb_dict = läsa_in_json_fil("område_ssyk_yb_struktur.json")

        områden = list(områdes_ssyk_yb_dict.keys())

        valt_yrkesområde = st.selectbox(
            "Eller välj ett yrkesområde som du tidigare har arbetat inom",
            (områden), index = None)
        
        if valt_yrkesområde:

            ssyk_info = områdes_ssyk_yb_dict.get(valt_yrkesområde)
            valbara_ssyk = []
            ssyk_yb = {}
            for s in ssyk_info:
                for k, v in s.items():
                    valbara_ssyk.append(k)
                    ssyk_yb[k] = v
            
            vald_yrkesgrupp = st.selectbox(
            "Välj en yrkesgrupp för att hitta olika yrken",
            (valbara_ssyk), index = None)

            valbara_yb = ssyk_yb.get(vald_yrkesgrupp)

            if vald_yrkesgrupp:
                valt_yrke = st.selectbox(
                    "Välj ett yrke som du tidigare har arbetat som",
                    (valbara_yb), index = None)
                if valt_yrke:
                    välja_yrke(valt_yrke, data, länsid)
        
def välja_utbildningsbakgrund(data, valt_län, länsid):
    utbildningsområden = []
    for i in data["susaområden_inriktningar"]:
        utbildningsområden.append(i["områdesnamn"])
        
    valt_utbildningsområde = st.selectbox(
        "Välj ett område som du har tidigare utbildning inom",
        (utbildningsområden), index = None)
    
    if valt_utbildningsområde:
        inriktningar_dict = {}
        for i in data["susaområden_inriktningar"]:
            if i["områdesnamn"] == valt_utbildningsområde:
                for k in i["inriktningar"]:
                    inriktningar_dict[k["inriktning"]] = k["id"]
        
        inriktningar = list(inriktningar_dict.keys())
    
        vald_utbildningsinriktning = st.selectbox(
            "Välj en inriktning som du har tidigare utbildning inom",
            (inriktningar), index = None)
        
        if vald_utbildningsinriktning:
            id_inriktning = str(inriktningar_dict.get(vald_utbildningsinriktning))

            col1, col2 = st.columns(2)

            with col1:
                erfarenhet_utb = st.radio(
                    f"Hur lång utbildning har du inom {vald_utbildningsinriktning}?",
                    ["kortare än 1 år", "längre än 1 år", "längre än 3 år"],
                    horizontal = True, index = None,
                )

            with col2:
                intresse_utb = st.radio(
                    f"Hur intresserad är du av att hitta ett yrke utifrån din utbildning inom {vald_utbildningsinriktning}?",
                    ["inte", "intresserad", "mycket"],
                    horizontal = True, index = None,
                )
            try:

                antal_att_visa_upp = 20
                info_vald_utb = data["susaid_topplista_skills"].get(id_inriktning)
                skills_vald_utb = info_vald_utb["skills"]
                skills = list(skills_vald_utb.keys())
                intresseord_utb = skills[0:antal_att_visa_upp]

                valda_intresseord_utb = st.multiselect(
                f"Välj ett eller flera ord som beskriver vad du är intresserad av",
                (intresseord_utb),)

                valda_erfarenhetsord_utb = []

                liknande_yb, liknande_yb_skills = cosine_mellan_bakgrund_och_alla_yrken(skills_vald_utb, intresse_utb, data)

                liknande_yb_med_prognos = addera_prognos_antal_annonser(liknande_yb, data, valt_län)

                st.write("Nedan finns länkar till annonser för några liknande yrken utifrån tillhörande yrkesgrupp och valda erfarenhets- och intresseord")

                col1, col2 = st.columns(2)

                antal = 0
                for i in liknande_yb:
                    try:
                        id_liknande_yrke = list(filter(lambda x: data["yrkesid_namn"][x] == i, data["yrkesid_namn"]))[0]
                        skills_liknande = liknande_yb_skills.get(i)
                        länk = skapa_länk_till_platsbanken(id_liknande_yrke, skills_liknande, valda_erfarenhetsord_utb, valda_intresseord_utb, data, länsid)
                        if (antal % 2) == 0:
                            col1.link_button(i, länk)
                        else:
                            col2.link_button(i, länk)
                        antal += 1
                    except:
                        pass

                st.button("Spara bakgrund", on_click = spara_data, args = (vald_utbildningsinriktning, valda_erfarenhetsord_utb, valda_intresseord_utb, liknande_yb))


                vald_liknande = st.selectbox(
                    "Välj ett liknande yrke som du skulle vilja veta mer om",
                    (liknande_yb_med_prognos),index = None)
            
                if vald_liknande:
                    vald_liknande_split = vald_liknande.split("(")
                    vald_liknande = vald_liknande_split[0]
                    skills_liknande = liknande_yb_skills.get(vald_liknande)
                    valda_ord = valda_erfarenhetsord_utb + valda_intresseord_utb
                    jämförelselista = skapa_jämförelselista(vald_utbildningsinriktning, skills_vald_utb, vald_liknande, skills_liknande, valda_ord)

                    id_liknande_yrke = list(filter(lambda x: data["yrkesid_namn"][x] == vald_liknande, data["yrkesid_namn"]))[0]

                    try:
                        af_kompetenser = data["yrkesid_topplista_taxonomibegrepp"].get(id_liknande_yrke)
                        if not af_kompetenser:
                            af_kompetenser = ["Kunde inte hitta någon data"]
                    except:
                        af_kompetenser = ["Kunde inte hitta någon data"]
                    taxonomi = ("  \n ").join(af_kompetenser)

                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"Till höger ser du kompetenser som många arbetsgivare efterfrågar när de söker efter en {vald_liknande}")

                    with col2:
                        st.write(taxonomi)

                    st.divider()

                    st.write(f"Nedanför ser du ord som många arbetsgivare använder i annonser för {vald_liknande}")

                    ordmoln = skapa_ordmoln(skills_liknande, skills_vald_utb, valda_erfarenhetsord_utb, valda_intresseord_utb)
                    st.pyplot(ordmoln)

                    st.divider()

                    st.write(f"Nedanför ser du likheter och skillnader mellan hur olika arbetsgivare och utbildningsanordnare uttrycker sig när det kommer till kunskaper, erfarenheter och arbetsuppgifter för {vald_utbildningsinriktning} och {vald_liknande}")

                    venn_data = jämföra_bakgrund_med_liknande(jämförelselista, valda_ord)
                    venn = skapa_venn(venn_data)
                    st.pyplot(venn)
            except:
                st.write("Finns inte tillräckligt med data")

def spara_data(vald_bakgrund, valda_erfarenhetsord, valda_intresseord, liknande):
    if vald_bakgrund not in st.session_state.bakgrunder:
        st.session_state.vald_bakgrund = True
        st.session_state.bakgrunder.append(vald_bakgrund)
        st.session_state.erfarenhetsord.extend(valda_erfarenhetsord)
        st.session_state.intresseord.extend(valda_intresseord)
        for i in liknande:
            st.session_state.liknande_yrken.append(i)

    with st.sidebar:
        rubrik = f"<p style='font-size:12px;font-weight: bold;'>Tillfälligt sparad data</p>"
        st.markdown(rubrik, unsafe_allow_html=True)

        bakgrundstext = "Sparade bakgrunder:\n"
        for i in st.session_state.bakgrunder:
            bakgrundstext += f"  {i}\n"
        bakgrundstext += "Sparade erfarenhetsord:\n"
        for i in st.session_state.erfarenhetsord:
            bakgrundstext += f"  {i}\n"
        bakgrundstext += "Sparade intresseord::\n"
        for i in st.session_state.intresseord:
            bakgrundstext += f"  {i}\n"
        text = f"<p style='font-size:12px;white-space: pre;'>{bakgrundstext}</p>"
        st.markdown(text, unsafe_allow_html=True)

all_data = läsa_in_json_fil("masterdata.json")
alla_länsid = läsa_in_json_fil("regionsnamn_id.json")

giltiga_län = list(all_data["länskod_länsnamn"].values())
giltiga_län = sorted(giltiga_län)

st.logo("af-logotyp-rgb-540px.jpg")

st.title("Demo")

st.write("Denna demo försöker utforska vad som går att säga utifrån annonsdata, utbildningsbeskrivningar, prognoser och arbetsmarknadstaxonomi. De fyra frågorna den försöker svar på är:\n1) VILKA liknande yrken finns det utifrån din yrkes- och utbildningsbakgrund?\n2) VARFÖR skulle ett liknande yrke passa just dig?\n3) HUR hittar du till annonser för dessa liknande yrken?\n4) VAD är bra för dig att lyfta fram i en ansökan till ett liknande yrke?")

instruktion = f"<p style='font-size:12px;'>Vill du starta om tryck cmd + r</p>"
st.markdown(instruktion, unsafe_allow_html=True)

if "vald_bakgrund" not in st.session_state:
    st.session_state.vald_bakgrund = False
    st.session_state.bakgrunder = []
    st.session_state.erfarenhetsord = []
    st.session_state.intresseord = []
    st.session_state.liknande_yrken = []

valt_län = st.selectbox(
    "Välj det län du huvudsakligen söker jobb i",
    (giltiga_län), index = None)

if len(st.session_state.bakgrunder) > 2:
    st.button("Testa om annons- och utbildningsdata kan hjälpa dig att upptäcka dina dolda kompetenser", on_click = None)

def ändra_state():
    st.session_state.vald_bakgrund = False

if st.session_state.vald_bakgrund == True:
    st.button("Lägga till fler yrkes- eller utbildningsbakgrunder", on_click = ändra_state)

if st.session_state.vald_bakgrund == False:
    yrke_utb_val = st.radio(
                f"Vill du jämföra din yrkes- eller utbildningsbakgrund mot liknande yrken?",
                ["yrkesbakgrund", "utbildningsbakgrund"],
                horizontal = True, index = 0,
        )

    if valt_län and yrke_utb_val == "yrkesbakgrund":
        länsid = alla_länsid.get(valt_län)
        välja_yrkesbakgrund(all_data, valt_län, länsid)

    elif valt_län and yrke_utb_val == "utbildningsbakgrund":
        länsid = alla_länsid.get(valt_län)
        välja_utbildningsbakgrund(all_data, valt_län, länsid)
