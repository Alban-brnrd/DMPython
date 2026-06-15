# =============================================================
# Application Streamlit - Espaces de Coworking à Paris
# Projet réalisé dans le cadre du cours d'introduction à Streamlit
# =============================================================

# On importe les bibliothèques dont on a besoin
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

# -----------------------------------------------------------
# CONFIGURATION DE LA PAGE
# Cette commande doit être la première instruction Streamlit
# -----------------------------------------------------------
st.set_page_config(
    page_title="Coworking Paris",
    page_icon="🏢",
    layout="wide"   # On utilise toute la largeur de la page
)

# -----------------------------------------------------------
# CHARGEMENT DES DONNÉES
# On utilise @st.cache_data pour ne pas recharger le fichier
# à chaque fois que l'utilisateur interagit avec l'appli
# -----------------------------------------------------------
@st.cache_data
def charger_donnees():
    # On lit le fichier CSV qui contient nos espaces de coworking
    df = pd.read_csv("pariscoworking.csv")
    return df

# On charge les données une fois pour toutes
df = charger_donnees()

# -----------------------------------------------------------
# EN-TÊTE DE L'APPLICATION
# -----------------------------------------------------------
st.title("🏢 Espaces de Coworking à Paris")
st.write(
    "Bienvenue ! Cette application vous aide à trouver un espace de "
    "coworking à Paris. Utilisez les filtres sur la gauche pour affiner "
    "votre recherche."
)

# Petite ligne de séparation
st.divider()

# -----------------------------------------------------------
# BARRE LATÉRALE (SIDEBAR) - Les filtres de recherche
# -----------------------------------------------------------
st.sidebar.title("🔍 Filtres de recherche")
st.sidebar.write("Affinez votre recherche ici :")

# Filtre 1 : Recherche par nom d'espace
recherche_nom = st.sidebar.text_input(
    "Rechercher par nom",
    placeholder="Ex: WeWork, Station F..."
)

# Filtre 2 : Sélection de l'arrondissement
# On récupère la liste des arrondissements disponibles dans les données
liste_arrondissements = sorted(df["arrondissement"].unique().tolist())

arrondissements_choisis = st.sidebar.multiselect(
    "Filtrer par arrondissement",
    options=liste_arrondissements,
    default=liste_arrondissements,  # Par défaut, tous sont sélectionnés
    format_func=lambda x: f"Paris {str(x)[-2:]}"  # Affiche "Paris 08" au lieu de "75008"
)

# Filtre 3 : Checkbox pour afficher les détails complets
afficher_details = st.sidebar.checkbox("Afficher les colonnes détaillées", value=False)

st.sidebar.divider()
st.sidebar.info("💡 **Astuce :** Cliquez sur un marqueur de la carte pour voir les infos de l'espace !")

# -----------------------------------------------------------
# APPLICATION DES FILTRES SUR LES DONNÉES
# -----------------------------------------------------------

# On part des données complètes
df_filtre = df.copy()

# On applique le filtre par arrondissement
if arrondissements_choisis:
    df_filtre = df_filtre[df_filtre["arrondissement"].isin(arrondissements_choisis)]

# On applique le filtre par nom (si l'utilisateur a tapé quelque chose)
if recherche_nom:
    df_filtre = df_filtre[
        df_filtre["titre"].str.contains(recherche_nom, case=False, na=False)
    ]

# -----------------------------------------------------------
# MÉTRIQUES - Un petit résumé en haut de la page
# -----------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Espaces trouvés",
        value=len(df_filtre),
        delta=f"sur {len(df)} au total"
    )

with col2:
    nb_arrondissements = df_filtre["arrondissement"].nunique()
    st.metric(
        label="Arrondissements couverts",
        value=nb_arrondissements
    )

with col3:
    # On compte les espaces qui ont un site web renseigné
    avec_site = df_filtre["siteweb"].notna().sum()
    st.metric(
        label="Avec site web",
        value=avec_site
    )

st.divider()

# -----------------------------------------------------------
# SECTION 1 : TABLEAU DES DONNÉES
# -----------------------------------------------------------
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
        # Version simplifiée pour une lecture rapide
        colonnes_a_afficher = ["titre", "arrondissement", "adresse", "telephone", "acces"]

    # On renomme les colonnes pour que ce soit plus lisible pour l'utilisateur
    noms_colonnes = {
        "titre": "Nom de l'espace",
        "arrondissement": "Arrondissement",
        "adresse": "Adresse",
        "telephone": "Téléphone",
        "acces": "Accès métro",
        "siteweb": "Site web",
        "description": "Description"
    }

    # On affiche le tableau avec les colonnes choisies
    st.dataframe(
        df_filtre[colonnes_a_afficher].rename(columns=noms_colonnes),
        use_container_width=True,   # Le tableau prend toute la largeur
        hide_index=True             # On cache l'index pour que ce soit plus propre
    )

    # On ajoute un bouton pour télécharger les données filtrées en CSV
    csv_export = df_filtre[colonnes_a_afficher].rename(columns=noms_colonnes).to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Télécharger cette liste en CSV",
        data=csv_export,
        file_name="coworking_paris_selection.csv",
        mime="text/csv"
    )

st.divider()

# -----------------------------------------------------------
# SECTION 2 : CARTE FOLIUM INTERACTIVE
# -----------------------------------------------------------
st.subheader("🗺️ Carte interactive des espaces")
st.write("Cliquez sur un marqueur pour voir les informations de l'espace de coworking.")

# On crée la carte centrée sur Paris
carte = folium.Map(
    location=[48.8566, 2.3522],   # Coordonnées du centre de Paris
    zoom_start=12
)

# On ajoute un marqueur pour chaque espace de coworking dans les données filtrées
for index, ligne in df_filtre.iterrows():

    # On vérifie que les coordonnées GPS existent bien pour cet espace
    if pd.notna(ligne["latitude"]) and pd.notna(ligne["longitude"]):

        # On prépare le contenu de la popup (la fenêtre qui s'ouvre au clic)
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

        # On ajoute le marqueur sur la carte
        folium.Marker(
            location=[ligne["latitude"], ligne["longitude"]],
            popup=folium.Popup(contenu_popup, max_width=250),
            tooltip=ligne["titre"],   # Le nom apparaît au survol de la souris
            icon=folium.Icon(
                color="blue",
                icon="briefcase",
                prefix="fa"
            )
        ).add_to(carte)

# On affiche la carte dans l'application Streamlit
folium_static(carte, width=1000, height=500)

st.divider()

# -----------------------------------------------------------
# SECTION 3 : QUELQUES STATISTIQUES
# -----------------------------------------------------------
st.subheader("📊 Répartition par arrondissement")

# On compte le nombre d'espaces par arrondissement
repartition = (
    df_filtre.groupby("arrondissement")
    .size()
    .reset_index(name="Nombre d'espaces")
)

# On formate l'arrondissement pour l'affichage
repartition["Arrondissement"] = repartition["arrondissement"].apply(
    lambda x: f"Paris {str(x)[-2:]}"
)

# On affiche le graphique en barres
st.bar_chart(
    repartition.set_index("Arrondissement")["Nombre d'espaces"]
)

# -----------------------------------------------------------
# PIED DE PAGE
# -----------------------------------------------------------
st.divider()
st.caption("Application réalisée avec Streamlit 🎈 | Données des espaces de coworking à Paris")
