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
import requests

@st.cache_data
def import_data(filename):
    with open(filename) as file:
        content = file.read()
    output = json.loads(content)
    return output

@st.cache_data
def create_small_wordcloud(skills_occupation):
    wordcloud = WordCloud(width=800, height=800,
                          background_color= 'white',
                          prefer_horizontal=1).generate_from_frequencies(skills_occupation)
    plt.figure(figsize = (3, 3), facecolor=None)
    plt.imshow(wordcloud)
    plt.axis('off')
    plt.tight_layout(pad=0)
    st.pyplot(plt)

@st.cache_data
def fetch_number_of_ads(url):
    response = requests.get(url)
    data = response.text
    json_data = json.loads(data)
    json_data_total = json_data["total"]
    number_of_ads = list(json_data_total.values())[0]
    return number_of_ads

@st.cache_data
def number_of_ads(ssyk_id, region_id, words):
    base = "https://jobsearch.api.jobtechdev.se/search?"
    end = "&limit=0"
    wordstring = "%20".join(words)
    string_words = "&q=" + wordstring
    if region_id:
        url = base + "occupation-group=" + ssyk_id + "&region=" + region_id + string_words + end
    else:
        url = base + "occupation-group=" + ssyk_id + string_words + end
    number_of_ads = fetch_number_of_ads(url)
    return number_of_ads

def create_words_of_interest(selected, similar):
    selected_skills = list(selected.keys())
    selected_skills = selected_skills[0:50]
    similar_skills = {}
    for value in similar.values():
        similar_skills = dict(Counter(similar_skills) + Counter(value))
    words_of_interest = []
    for i in similar_skills:
        if not i in selected_skills:
            words_of_interest.append(i)
    return words_of_interest

def show_wordcloud_selected_occupation(occupation, id, data):
    with st.sidebar:
        headline = f"<p style='font-size:12px;'>Ord som förekommer i annonser för {occupation}</p>"
        st.markdown(headline, unsafe_allow_html=True)
        info_selected_occupation = data["yrkesid_topplista_skills"].get(id)
        skills_selected_occupation = info_selected_occupation["skills"]
        skills_selected_occupation = dict(itertools.islice(skills_selected_occupation.items(),30))
        create_small_wordcloud(skills_selected_occupation)

        area = data["yrkesid_område"].get(id)
        ssyk_id = data["yrkesid_ssykid"].get(id)


        PIPE = "│"
        ELBOW = "└──"
        SHORT_ELBOW = "└─"
        LONG_ELBOW = "    └──"
        TEE = "├──"
        PIPE_PREFIX = "│   "
        SPACE_PREFIX = "&nbsp;&nbsp;&nbsp;&nbsp;"

        träd = f"<p style='font-size:12px;'>{area} (yrkesområde)<br />{SHORT_ELBOW}{ssyk_id} (yrkesgrupp)<br />{SPACE_PREFIX}{SHORT_ELBOW}{occupation} (yrkesbenämning)</p>"
        st.markdown(träd, unsafe_allow_html=True)

def create_comparable_lists(name_selected, skills_selected, name_similar, skills_similar, selected_words):
    output = []
    skills_selected = list(skills_selected.keys())
    for s in skills_selected:
        if s in selected_words:
            try:
                index_to_move_from = skills_selected.index(s)
                skill_to_move = skills_selected.pop(index_to_move_from)
                skills_selected.insert(0, skill_to_move)
            except:
                pass
    background = {"name": name_selected,
                "skills": skills_selected}
    output.append(background)
    skills_similar = list(skills_similar.keys())
    for k in skills_similar:
        if k in selected_words:
            try:
                index_to_move_from = skills_selected.index(k)
                skill_to_move = skills_selected.pop(index_to_move_from)
                skills_selected.insert(0, skill_to_move)
            except:
                pass
    similar = {"name": name_similar,
               "skills": skills_similar}
    output.append(similar)
    return output

def add_forecast_addnumbers(occupation, id, ssyk, words, data, region_id):
    forecast_lan = "00"
    try:
        forecast = data["yrkesid_länskod_prognos"].get(id)
        for p in forecast:
            if p["län"] == forecast_lan:
                similar_forecast = p["prognos"]
        if similar_forecast == "små":
            pil = "\u2193"
        elif similar_forecast == "medelstora":
            pil = "\u2192"
        elif similar_forecast == "stora":
            pil = "\u2191"
        else:
            pil = ""
        addnumber = number_of_ads(ssyk, region_id, words)
        return str(f"{occupation}({addnumber}){pil}"), str(f"{occupation}({addnumber})"), str(f"{occupation}({pil})")
    except:
        return occupation

def convert_text(text):
    text = text.strip()
    text = text.lower()
    to_convert = {
        " ": "%20",
        "\^": "%5E",
        "'": "%22"}
    for key, value in to_convert.items():
        text = re.sub(key, value, text)
    return text

def create_link(ssyk_id, keywords, region_id):
    base = f"https://arbetsformedlingen.se/platsbanken/annonser?p=5:{ssyk_id}&q="
    keywords_split = []
    for s in keywords:
        s = convert_text(s)
        keywords_split.append(s)
    keywords_split = "%20".join(keywords_split)
    if region_id:
        region = "&l=2:" + region_id
        return base + keywords_split + region
    else:
        return base + keywords_split

def create_keywords(skills, words):
    number_to_save = 15
    listed_skills = list(skills.keys())
    all_skills = words + listed_skills
    keywords = all_skills[0:number_to_save]
    return keywords

def create_similar_occupations(id_selected, skills_selected, level_area_interest, input):
    all_similar = {}
    similar_data = input["yrkesid_topplista_liknande"].get(id_selected)
    if level_area_interest == "inte intresserad":
        number_same_area = 0
        number_other_area = 4
    elif level_area_interest == "":
        number_same_area = 2
        number_other_area = 2
    elif level_area_interest == "mycket intresserad":
        number_same_area = 4
        number_other_area = 0
    number_added = 0
    while number_added < number_same_area:
        try:
            similar_occupation_id = similar_data["liknande_samma_område"][number_added]
            similar_name = input["yrkesid_namn"].get(similar_occupation_id)
            info_similar = input["yrkesid_topplista_skills"].get(similar_occupation_id)
            if info_similar:
                all_similar[similar_name] = info_similar["skills"]
            number_added += 1
        except:
            number_added += 1
    number_added = 0
    while number_added < number_other_area:
        try:
            similar_occupation_id = similar_data["liknande_annat_område"][number_added]
            similar_name = input["yrkesid_namn"].get(similar_occupation_id)
            info_similar = input["yrkesid_topplista_skills"].get(similar_occupation_id)
            if info_similar:
                all_similar[similar_name] = info_similar["skills"]
            number_added += 1
        except:
            number_added += 1
    words_of_interest = create_words_of_interest(skills_selected, all_similar)
    return all_similar, words_of_interest   

def create_venn(indata):
    titles = []
    skills = []
    for k, v in indata.items():
        if k:
            titles.append(k)
        if v:
            skills.append(set(v))
    plt.figure(figsize= (12, 8))
    venn = venn2(subsets = skills, set_labels = titles, set_colors = ["skyblue", "lightgreen"])
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

def count_frequency(data):
    output = {}
    data = Counter(data)
    for k, a in data.items():
        output[k] = a
    return output

def compare_background_and_similar(input, words):
    output = {}
    all_skills = []
    unique_skills = []
    overlapping_skills = []
    for i in input:
        all_skills = all_skills + i["skills"]
    all_skills = count_frequency(all_skills)
    for k, v in all_skills.items():
        if v == 1:
            unique_skills.append(k)
    for i in input:
        number_of_unique = 0
        number_added = 0
        number_overlapping = 0
        output[i["name"]] = []
        for s in i["skills"]:
            if s in unique_skills:
                if number_of_unique < 11:
                    if s in words:
                        output[i["name"]].append(f"\u00BB{s}")
                    else:
                        output[i["name"]].append(s)
                    number_added += 1
                    number_of_unique += 1
            else:
                if number_overlapping < 11:
                    overlapping_skills.append(s)
                    number_added += 1
                    number_overlapping += 1
    for i in input:
        for s in i["skills"]:
            if s in overlapping_skills:
                if s in words:
                    output[i["name"]].append(f"\u00BB{s}")
                else:
                    output[i["name"]].append(s)
    return output

def compare_background_similar(id_selected, skills_selected, similar_forecast, similiar_with_skills, words_of_experience, words_of_interest, input):
        selected_occupation = input["yrkesid_namn"].get(id_selected)
        selected_similar = st.selectbox(
            "Välj ett liknande yrke som du skulle vilja veta mer om",
            (similar_forecast),index = None)
        
        if selected_similar:
            # selected_similar_split = selected_similar.split("(")
            # selected_similar = selected_similar_split[0]
            skills_selected_similar = similiar_with_skills.get(selected_similar)
            selected_words = words_of_experience + words_of_interest
            comparable_list = create_comparable_lists(selected_occupation, skills_selected, selected_similar, skills_selected_similar, selected_words)

            st.write(f"Nedanför ser du likheter och skillnader mellan hur olika arbetsgivare och utbildningsanordnare uttrycker sig när det kommer till kunskaper, erfarenheter och arbetsuppgifter för {selected_occupation} och {selected_similar}")

            venn_data = compare_background_and_similar(comparable_list, selected_words)
            venn = create_venn(venn_data)
            st.pyplot(venn)

            st.divider()

            id_selected_similar = list(filter(lambda x: input["yrkesid_namn"][x] == selected_similar, input["yrkesid_namn"]))[0]
            descriptions = import_data("id_yrkesbeskrivningar.json")
            similar_description = descriptions.get(id_selected_similar)

            try:
                af_competences = input["yrkesid_topplista_taxonomibegrepp"].get(id_selected_similar)
                if not af_competences:
                    af_competences = ["Kunde inte hitta någon data"]
            except:
                af_competences = ["Kunde inte hitta någon data"]
            taxonomy = ("  \n ").join(af_competences)

            st.write(selected_similar)
            st.write(similar_description)

            col1, col2 = st.columns(2)

            with col1:
                st.write(f"Ord som förekommer i annonser")
                create_small_wordcloud(skills_selected_similar)

            with col2:
                st.write(f"Efterfrågade kompetenser")
                st.write("")
                st.write(taxonomy)


def select_experience_interests(selected_occupation, data):
    jobtitles_id = import_data("titlar_yb_id.json")
    id_selected_occupation = jobtitles_id.get(selected_occupation)
    area = data["yrkesid_område"].get(id_selected_occupation)

    col1, col2 = st.columns(2)

    with col1:
        selected_interest_education = st.slider(
            f"Hur många år skulle du kunna tänka dig studera för att hitta ett annat yrke? OBS! Inte implementerad än", 0, 4, 0,
        )

    with col2:
        selected_interest_area = st.select_slider(
            f"Hur intresserad är du av yrken inom yrkesområdet {area}?",
            ["inte intresserad", "", "mycket intresserad"],
            value = "",
        )

    number_to_display = 20
    info_selected_occupation = data["yrkesid_topplista_skills"].get(id_selected_occupation)
    skills_selected_occupation = info_selected_occupation["skills"]
    list_skills_selected_occupation = list(skills_selected_occupation.keys())
    words_of_experience = list_skills_selected_occupation[0:number_to_display]

    selected_words_of_experience = st.multiselect(
        f"Här är en lista på några ord från annonser för {selected_occupation}. Välj ett eller flera ord som beskriver vad du är bra på.",
        (words_of_experience),)

    all_similar, words_of_interest = create_similar_occupations(id_selected_occupation, skills_selected_occupation, selected_interest_area, data)

    words_of_interest = words_of_interest[0:number_to_display]
    selected_words_of_interest = st.multiselect(
        f"Här kommer en lista på några ord från annonser för yrkesbenämningar som på ett eller annat sätt liknar det du tidigare har jobbat med. Välj ett eller flera ord som beskriver vad du är intresserad av.",
        (words_of_interest),)
    
    col1, col2 = st.columns(2)

    with col1:
        work_experience = st.select_slider(
            f"Hur erfaren är du som {selected_occupation}?",
            ["oerfaren", "", "mycket erfaren"],
            value = "",
        )

    with col2:
        st.button("Spara bakgrund och börja om från början", on_click = save_selections, args = (selected_occupation, selected_words_of_experience, selected_words_of_interest, all_similar))

        regional_data = data["länskod_länsnamn"]
        valid_regions = list(regional_data.values())
        valid_regions = sorted(valid_regions)

        selected_region = st.selectbox(
            "Begränsa sökområde till ett län",
            (valid_regions), index = None)

    st.divider()

    st.write("Nedan finns länkar till annonser för några liknande yrken utifrån tillhörande yrkesgrupp och valda erfarenhets- och intresseord")

    col1, col2 = st.columns(2)

    number = 0
    descriptions = import_data("id_yrkesbeskrivningar.json")
    forecasts = import_data("yrke_barometer_alla.json")
    similar_with_forecast = []
    similar_names = []
    if selected_region:
        regional_id = import_data("regionsnamn_id.json")
        selected_regional_id = regional_id.get(selected_region)
        regional_number = list(filter(lambda x: regional_data[x] == selected_region, regional_data))[0]
    else:
        regional_number = "00"
        selected_regional_id = None
    for key, value in all_similar.items():
        try:
            similar_names.append(key)
            id_similar = list(filter(lambda x: data["yrkesid_namn"][x] == key, data["yrkesid_namn"]))[0]
            similar_description = descriptions.get(id_similar)
            similar_forecast = forecasts.get(id_similar)
            for f in similar_forecast:
                if f["region"] == regional_number:
                    regional_forecast_text = f["text"]
            skills = value
            ssyk_id = data["yrkesid_ssykid"].get(id_similar)
            keywords = create_keywords(skills, selected_words_of_experience + selected_words_of_interest)
            name_with_addnumbers_forecast,  name_with_addnumbers, name_with_forecast = add_forecast_addnumbers(key, id_similar, ssyk_id, keywords, data, selected_regional_id)
            similar_with_forecast.append(name_with_forecast)
            
            link = create_link(ssyk_id, keywords, selected_regional_id)
            if (number % 2) == 0:
                col1.link_button(name_with_addnumbers_forecast, link, help = regional_forecast_text)
            else:
                col2.link_button(name_with_addnumbers_forecast, link, help = regional_forecast_text)
            number += 1
        except:
            pass
    
    compare_background_similar(id_selected_occupation, skills_selected_occupation, similar_names, all_similar, selected_words_of_experience, selected_words_of_interest, data)

def save_selections(occupation, experience, interest, similar):
    if occupation not in st.session_state.stored_backgrounds:
        st.session_state.chosen_background = True
        st.session_state.stored_backgrounds.append(occupation)
        st.session_state.words_of_experience.extend(experience)
        st.session_state.words_of_interest.extend(interest)
        for key in similar.keys():
            st.session_state.similar_occupations.append(key)

    with st.sidebar:
        rubrik = f"<p style='font-size:12px;font-weight: bold;'>Tillfälligt sparad data</p>"
        st.markdown(rubrik, unsafe_allow_html=True)
        bakgrundstext = "Sparade bakgrunder:\n"
        for i in st.session_state.stored_backgrounds:
            bakgrundstext += f"  {i}\n"
        bakgrundstext += "Sparade erfarenhetsord:\n"
        for i in st.session_state.words_of_experience:
            bakgrundstext += f"  {i}\n"
        bakgrundstext += "Sparade intresseord::\n"
        for i in st.session_state.words_of_interest:
            bakgrundstext += f"  {i}\n"
        text = f"<p style='font-size:12px;white-space: pre;'>{bakgrundstext}</p>"
        st.markdown(text, unsafe_allow_html=True)

def change_state_chosen_background():
    st.session_state.chosen_background = False

def select_occupational_background(input, occupation_or_area):
    valid_occupations = import_data("giltiga_titlar_yb.json")
    valid_occupations = sorted(valid_occupations)
    jobtitles_id = import_data("titlar_yb_id.json")

    if occupation_or_area == "välja yrke":
   
        selected_occupation = st.selectbox(
            "Välj ett yrke som du tidigare har arbetat som",
            (valid_occupations), placeholder = "", index = None)

        if selected_occupation:
            id_selected_occupation = jobtitles_id.get(selected_occupation)
            occupation_name = input["yrkesid_namn"].get(id_selected_occupation)
            show_wordcloud_selected_occupation(occupation_name, id_selected_occupation, input)
            select_experience_interests(selected_occupation, input)

    if occupation_or_area == "välja yrkesområde":
        area_ssyk_dict = import_data("område_ssyk_yb_struktur.json")
        areas = list(area_ssyk_dict.keys())
        areas = sorted(areas)

        selected_area = st.selectbox(
            "Välj ett yrkesområde som du tidigare har arbetat inom",
            (areas), index = None)

        if selected_area:

            ssyk_info = area_ssyk_dict.get(selected_area)
            valid_ssyk = []
            ssyk_occupations = {}
            for s in ssyk_info:
                for k, v in s.items():
                    valid_ssyk.append(k)
                    ssyk_occupations[k] = v
            valid_ssyk = sorted(valid_ssyk)

            selected_ssyk = st.selectbox(
            "Välj en yrkesgrupp för att hitta olika yrken",
            (valid_ssyk), index = None)

            valid_occupations_ssyk = ssyk_occupations.get(selected_ssyk)

            if selected_ssyk:
                selected_occupation_ssyk = st.selectbox(
                    "Välj ett yrke som du tidigare har arbetat som",
                    (valid_occupations_ssyk), placeholder = "", index = None)

                if selected_occupation_ssyk:
                    id_selected_occupation = jobtitles_id.get(selected_occupation_ssyk)
                    show_wordcloud_selected_occupation(selected_occupation_ssyk, id_selected_occupation, input)
                    select_experience_interests(selected_occupation_ssyk, input)

def select_educational_background(data):
    educational_areas = []
    for i in data["susaområden_inriktningar"]:
        educational_areas.append(i["områdesnamn"])
    
    educational_areas = sorted(educational_areas)

    selected_educational_area = st.selectbox(
        "Välj ett område som du har tidigare utbildning inom",
        (educational_areas), index = None)
    
    if selected_educational_area:
        focus_dict = {}
        for i in data["susaområden_inriktningar"]:
            if i["områdesnamn"] == selected_educational_area:
                for k in i["inriktningar"]:
                    focus_dict[k["inriktning"]] = k["id"]
        
        educational_focus = list(focus_dict.keys())
        educational_focus = sorted(educational_focus)
    
        selected_educational_focus = st.selectbox(
            "Välj en inriktning som du har tidigare utbildning inom",
            (educational_focus), index = None)
        
        if selected_educational_focus:
            id_focus = str(focus_dict.get(selected_educational_focus))

            try:
                number_to_display = 20
                info_selected_education = data["susaid_topplista_skills"].get(id_focus)
                skills_selected_education = info_selected_education["skills"]
                list_skills_selected_education = list(skills_selected_education.keys())
                words_of_experience_education = list_skills_selected_education[0:number_to_display]

                selected_words_of_experience_education = st.multiselect(
                    f"Välj ett eller flera ord som beskriver vad du har mycket kunskap om eller är intresserad av.",
                    (words_of_experience_education),)
    
            except:
                st.write("Finns inte tillräckligt med data")

st.logo("af-logotyp-rgb-540px.jpg")

st.title("Demo")

text1 = "Denna demo försöker utforska vad som går att säga utifrån annonsdata, utbildningsbeskrivningar, prognoser och arbetsmarknadstaxonomi. De fyra frågorna den försöker svar på är: 1) VILKA liknande yrken finns det utifrån din yrkes- och utbildningsbakgrund? 2) VARFÖR skulle ett liknande yrke passa just dig? 3) HUR hittar du till annonser för dessa liknande yrken? 4) VAD är bra för dig att lyfta fram i en ansökan till ett liknande yrke? Vill du starta om tryck cmd + r"

st.markdown(f"<p style='font-size:12px;'>{text1}</p>", unsafe_allow_html=True)

if "chosen_background" not in st.session_state:
    st.session_state.chosen_background = False
    st.session_state.stored_backgrounds = []
    st.session_state.words_of_experience = []
    st.session_state.words_of_interest = []
    st.session_state.similar_occupations = []

if len(st.session_state.stored_backgrounds) > 2:
    st.button("Testa om annons- och utbildningsdata kan hjälpa dig att upptäcka dina dolda kompetenser") #on_click = ?

if st.session_state.chosen_background == True:
    st.button("Lägga till fler yrkes- eller utbildningsbakgrunder", on_click = change_state_chosen_background)

masterdata = import_data("masterdata.json")

if st.session_state.chosen_background == False:
    col1, col2 = st.columns(2)
    with col1:
        occupational_or_educational = st.radio(
                    f"Utgå från yrkes- eller utbildningsbakgrund",
                    ["yrkesbakgrund", "utbildningsbakgrund"],
                    horizontal = True, index = 0,
            )

    with col2:
        if occupational_or_educational == "yrkesbakgrund":
            name_or_area = st.radio(
            f"Välj yrke direkt eller orientera utifrån yrkesområde?",
            ["välja yrke", "välja yrkesområde"],
            horizontal = True, index = 0,
        )

    if occupational_or_educational == "yrkesbakgrund":
        select_occupational_background(masterdata, name_or_area)

    if occupational_or_educational == "utbildningsbakgrund":
        select_educational_background(masterdata)
