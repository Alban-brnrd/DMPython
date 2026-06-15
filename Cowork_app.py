# Devoir Maison - Streamlit & Folium - Alban BERNARD

#Chargement des bibliothèques nécessaires
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static

#Création de la page
st.set_page_config(
    page_title="Coworking Paris",
    page_icon="🏢",
    layout="wide"   # On utilise toute la largeur de la page
)

# Chargement des données en cache
@st.cache_data
def charger_donnees():
    # On lit le fichier CSV qui contient nos espaces de coworking
    df = pd.read_csv("pariscoworking.csv")
    return df

df = charger_donnees()
df["station"] = df["acces"].str.replace("Métro ", "").str.split("(").str[0].str.strip()

# En-tête du site Streamlit

st.title("Espaces de Coworking à Paris")
st.write(
    "Bienvenue ! Cette application vous aide à trouver un espace de "
    "coworking à Paris. N'hésitez pas à utiliser les filtres sur la gauche pour affiner "
    "votre recherche."
)
st.divider()

# Barre latérale avec filtres
st.sidebar.title("Filtres de recherche")
st.sidebar.write("Affinez votre recherche ici :")

# Filtre 1 : Recherche par nom d'espace
recherche_nom = st.sidebar.text_input(
    "Rechercher par nom",
    placeholder="Ex: WeWork, Station F..."
)

# Filtre 2 : Sélection de l'arrondissement
liste_arrondissements = sorted(df["arrondissement"].unique().tolist())

arrondissements_choisis = st.sidebar.multiselect(
    "Filtrer par arrondissement",
    options=liste_arrondissements,
    default=liste_arrondissements,
    format_func=lambda x: f"Paris {str(x)[-2:]}"  # Affiche "Paris 08" au lieu de "75008"
)
# Filtre 3 : Filtre par métro
liste_stations = sorted(df["station"].unique().tolist())

stations_choisies = st.sidebar.multiselect(
    "Filtrer par station de métro",
    options=liste_stations,
    default=liste_stations
)

# Filtre 4 : Checkbox pour afficher plus d'informations
afficher_details = st.sidebar.checkbox("Afficher les colonnes détaillées", value=False)

st.sidebar.divider()
st.sidebar.info("**Astuce :** Cliquez sur un marqueur de la carte pour voir les infos de l'espace !")

df_filtre = df.copy()


# Application du filtre par arrondissement
if arrondissements_choisis:
    df_filtre = df_filtre[df_filtre["arrondissement"].isin(arrondissements_choisis)]

# Application du filtre par nom
if recherche_nom:
    df_filtre = df_filtre[
        df_filtre["titre"].str.contains(recherche_nom, case=False, na=False)
    ]
# Application du filtre par métro
df_filtre["station"] = df_filtre["acces"].str.replace("Métro ", "").str.split("(").str[0].str.strip()
if stations_choisies:
    df_filtre = df_filtre[df_filtre["station"].isin(stations_choisies)]

# KPI
col1, col2, col3 = st.columns(3)

# Nombre d'espace de cowork
with col1:
    st.metric(
        label="Espaces trouvés",
        value=len(df_filtre),
        delta=f"sur {len(df)} au total"
    )

# Nombre d'arrondissements
with col2:
    nb_arrondissements = df_filtre["arrondissement"].nunique()
    st.metric(
        label="Arrondissements couverts",
        value=nb_arrondissements
    )

# Nombre de cowork avec un lien
with col3:
    # On compte les espaces qui ont un site web renseigné
    avec_site = df_filtre["siteweb"].notna().sum()
    st.metric(
        label="Avec site web",
        value=avec_site
    )

st.divider()

# Passage à la partie Tableau
st.subheader("📋 Liste des espaces de coworking")

# On vérifie qu'il y a bien des résultats à afficher
if len(df_filtre) == 0:
    st.warning("Aucun espace de coworking trouvé avec ces critères. Essayez d'élargir votre recherche !")
else:
    # On choisit les colonnes à afficher selon la checkbox
    if afficher_details:
        # Version détaillée avec toutes les colonnes utiles
        colonnes_a_afficher = ["titre", "arrondissement", "adresse", "telephone", "acces", "siteweb", "description"]
    else:
        # Version simplifiée
        colonnes_a_afficher = ["titre", "arrondissement", "adresse", "telephone", "acces"]

    # Renommage
    noms_colonnes = {
        "titre": "Nom de l'espace",
        "arrondissement": "Arrondissement",
        "adresse": "Adresse",
        "telephone": "Téléphone",
        "acces": "Accès métro",
        "siteweb": "Site web",
        "description": "Description"
    }

    st.dataframe(
        df_filtre[colonnes_a_afficher].rename(columns=noms_colonnes),
        use_container_width=True,   
        hide_index=True             
    )

    csv_export = df_filtre[colonnes_a_afficher].rename(columns=noms_colonnes).to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Télécharger cette liste en CSV",
        data=csv_export,
        file_name="coworking_paris_selection.csv",
        mime="text/csv"
    )

st.divider()

# Carte Folium
st.subheader("🗺️ Carte interactive des espaces")
st.write("Cliquez sur un marqueur pour voir les informations de l'espace de coworking.")

carte = folium.Map(
    location=[48.8566, 2.3522],   # Coordonnées de Paris centre
    zoom_start=12
)

for index, ligne in df_filtre.iterrows():

    # On vérifie que les coordonnées GPS existent bien pour cet espace
    if pd.notna(ligne["latitude"]) and pd.notna(ligne["longitude"]):
        # On gère le cas où le numéro de téléphone n'est pas renseigné
        telephone_affiche = ligne["telephone"] if pd.notna(ligne["telephone"]) else "Non renseigné"
        # On crée le contenu HTML de la popup
        contenu_popup = f"""
        <div style="font-family: Arial; width: 220px;">
            <h4 style="color: #1f77b4; margin-bottom: 5px;">{ligne['titre']}</h4>
            <p style="margin: 3px 0;"><b>📍</b> {ligne['adresse']}</p>
            <p style="margin: 3px 0;"><b>🚇</b> {ligne['acces']}</p>
            <p style="margin: 3px 0;"><b>📞</b> {telephone_affiche}</p>
            <p style="margin: 5px 0; font-size: 0.85em; color: #555;">{ligne['description'][:100]}...</p>
            <a href="{ligne['siteweb']}" target="_blank" style="color: #1f77b4;">
                🔗 Voir le site web
            </a>
        </div>
        """

        folium.Marker(
            location=[ligne["latitude"], ligne["longitude"]],
            popup=folium.Popup(contenu_popup, max_width=250),
            tooltip=ligne["titre"],   
            icon=folium.Icon(
                color="blue",
                icon="briefcase",
                prefix="fa"
            )
        ).add_to(carte)

# On affiche la carte dans l'application Streamlit
folium_static(carte, width=1000, height=500)

st.divider()

# Statistiques
col_graph1, col_graph2 = st.columns(2)

# Graphie bar chart cowork par arrondissement
with col_graph1:
    st.subheader("📊 Répartition par arrondissement")
    repartition = df_filtre.groupby("arrondissement").size().reset_index()
    repartition.columns = ["arrondissement", "nb_espaces"]
    repartition["Arrondissement"] = repartition["arrondissement"].apply(
        lambda x: f"Paris {str(x)[-2:]}"
    )
    st.bar_chart(repartition.set_index("Arrondissement")["nb_espaces"])

# Graphique pie chart cowork par métro
with col_graph2:
    st.subheader("🚇 Répartition par station de métro")
    repartition_metro = df_filtre.groupby("station").size()

    fig, ax = plt.subplots()
    ax.pie(
        repartition_metro.values,
        labels=repartition_metro.index,
        autopct="%1.0f%%",
        startangle=90
    )
    ax.axis("equal")
    st.pyplot(fig)

# Pied de page
st.divider()
st.caption("Application réalisée avec Streamlit / Données des espaces de coworking à Paris")
