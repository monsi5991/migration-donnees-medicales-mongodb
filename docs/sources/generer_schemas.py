"""Génère les 4 schémas du projet en SVG (rendus ensuite en PNG avec Chrome headless)."""
import os
import sys
from xml.sax.saxutils import escape

OUT = sys.argv[1]
SANS = "Helvetica Neue, Helvetica, Arial, sans-serif"
MONO = "Menlo, Monaco, monospace"

INK, MUTED, LINE = "#1d2733", "#5b6776", "#c9d1db"
GREEN, GREEN_BG = "#00684A", "#e6f4ee"
BLUE, BLUE_BG = "#2f6aa3", "#e8f0f9"
AMBER, AMBER_BG = "#a86a00", "#fdf3e1"
RED, RED_BG = "#b3261e", "#fbe9e7"
GRAY_BG = "#f4f6f8"


def svg(w, h, body, title, subtitle):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs>
  <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker>
  <marker id="arrg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker>
</defs>
<rect width="100%" height="100%" fill="#ffffff"/>
<text x="40" y="48" font-family="{SANS}" font-size="28" font-weight="700" fill="{INK}">{escape(title)}</text>
<text x="40" y="76" font-family="{SANS}" font-size="16" fill="{MUTED}">{escape(subtitle)}</text>
{body}
</svg>"""


def text(x, y, s, size=15, color=INK, weight="400", family=SANS, anchor="start", style="normal"):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}" font-style="{style}">{escape(s)}</text>')


def rect(x, y, w, h, fill, stroke, r=12, dash=None, sw=2):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'


def line(points, color=INK, marker="arr", dash=None, sw=2):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#{marker})"' if marker else ""
    pts = " ".join(f"{x},{y}" for x, y in points)
    return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{sw}"{d}{m}/>'


def card(x, y, w, h, title, lines, color, bg, title_size=18, line_size=14, mono_lines=False):
    out = [rect(x, y, w, h, bg, color), text(x + 18, y + 32, title, title_size, color, "700")]
    for i, s in enumerate(lines):
        out.append(text(x + 18, y + 60 + i * 22, s, line_size, INK, family=MONO if mono_lines else SANS))
    return "\n".join(out)


def cylinder(x, y, w, h, title, sub, color, bg):
    ry = 12
    return "\n".join([
        f'<path d="M{x},{y + ry} L{x},{y + h - ry} A{w / 2},{ry} 0 0 0 {x + w},{y + h - ry} '
        f'L{x + w},{y + ry}" fill="{bg}" stroke="{color}" stroke-width="2"/>',
        f'<ellipse cx="{x + w / 2}" cy="{y + ry}" rx="{w / 2}" ry="{ry}" fill="{bg}" stroke="{color}" stroke-width="2"/>',
        text(x + w / 2, y + 52, title, 17, color, "700", anchor="middle"),
        text(x + w / 2, y + 76, sub, 13, MUTED, anchor="middle", family=MONO),
    ])


def pill(x, y, s, color, bg):
    w = 9 * len(s) + 18
    return rect(x, y - 16, w, 22, bg, color, r=11, sw=1) + text(x + w / 2, y, s, 13, color, "700", MONO, "middle")


# ---------------------------------------------------------------- 1. schéma de la base
def schema_base():
    b = []
    X, W = 40, 880
    b.append(rect(X, 105, W, 760, GRAY_BG, LINE))
    b.append(text(X + 20, 138, "Collection healthcare.admissions : 1 document = 1 séjour", 18, INK, "700"))
    b.append(text(X + W - 42, 138, "colonne du CSV", 13, MUTED, anchor="end", style="italic"))

    TYPE_X, SRC_X = 590, X + W - 42
    colors = {"string": (BLUE, BLUE_BG), "int": (GREEN, GREEN_BG), "double": (GREEN, GREEN_BG),
              "date": (AMBER, AMBER_BG), "ObjectId": (MUTED, "#ffffff")}

    def field(x, y, name, typ, src):
        c, bg = colors[typ]
        return "\n".join([text(x, y, name, 16, INK, "600", MONO), pill(TYPE_X, y, typ, c, bg),
                          text(SRC_X, y, src, 13, MUTED, anchor="end", style="italic")])

    y = 180
    b.append(field(X + 30, y, "_id", "ObjectId", "(créé par MongoDB)"))

    def sub(y, name, color, bg, fields):
        h = 44 + 30 * len(fields)
        out = [rect(X + 20, y, W - 40, h, bg, color, r=10),
               text(X + 38, y + 28, name, 16, color, "700", MONO),
               text(X + 38 + 10 * len(name) + 8, y + 28, "sous-document", 13, MUTED, style="italic")]
        for i, (n, t, s) in enumerate(fields):
            out.append(field(X + 60, y + 58 + 30 * i, n, t, s))
        return "\n".join(out), y + h

    s, y = sub(200, "patient", BLUE, "#ffffff", [
        ("name", "string", "Name (normalisé)"), ("age", "int", "Age"),
        ("gender", "string", "Gender"), ("blood_type", "string", "Blood Type")])
    b.append(s)
    b.append(field(X + 30, y + 32, "medical_condition", "string", "Medical Condition"))
    s, y = sub(y + 52, "admission", AMBER, "#ffffff", [
        ("date", "date", "Date of Admission"), ("type", "string", "Admission Type"),
        ("discharge_date", "date", "Discharge Date"), ("room_number", "int", "Room Number"),
        ("doctor", "string", "Doctor"), ("hospital", "string", "Hospital (virgule retirée)")])
    b.append(s)
    s, y = sub(y + 20, "billing", GREEN, "#ffffff", [
        ("amount", "double", "Billing Amount (2 déc.)"), ("insurance_provider", "string", "Insurance Provider")])
    b.append(s)
    b.append(field(X + 30, y + 32, "medication", "string", "Medication"))
    b.append(field(X + 30, y + 62, "test_results", "string", "Test Results"))

    RX, RW = 960, 400
    b.append(card(RX, 105, RW, 250, "Index", [], GREEN, GREEN_BG))
    for i, (n, f) in enumerate([("_id_", "(automatique)"), ("idx_patient_name", "patient.name"),
                                ("idx_medical_condition", "medical_condition"),
                                ("idx_admission_date", "admission.date"), ("idx_hospital", "admission.hospital")]):
        b.append(text(RX + 18, 165 + 30 * i, n, 13, INK, "700", MONO))
        b.append(text(RX + 215, 165 + 30 * i, f, 13, MUTED, family=MONO))
    b.append(text(RX + 18, 335, "Accélèrent les recherches les plus fréquentes.", 13, MUTED))
    b.append(card(RX, 380, RW, 250, "Choix de modélisation", [
        "• Sous-documents : les champs liés sont",
        "  regroupés (patient, admission, billing).",
        "• Noms en anglais, snake_case.",
        "• Types BSON vérifiés après migration ($type).",
        "• 55 500 lignes – 534 doublons exacts",
        "  = 54 966 documents.",
        "• Pas de schéma imposé par MongoDB : c'est",
        "  le script qui garantit la structure."], BLUE, BLUE_BG, line_size=14))
    b.append(card(RX, 655, RW, 210, "Types BSON", [], INK, "#ffffff"))
    for i, (t, d) in enumerate([("string", "texte"), ("int", "entier (32 bits)"),
                                ("double", "nombre décimal"), ("date", "date (ISODate, UTC)")]):
        c, bg = colors[t]
        b.append(pill(RX + 22, 715 + 36 * i, t, c, bg))
        b.append(text(RX + 130, 715 + 36 * i, d, 15))
    return svg(1400, 900, "\n".join(b), "Schéma de la base MongoDB",
               "Base healthcare · collection admissions · structure d'un document et origine de chaque champ")


# ---------------------------------------------------------------- 2. architecture docker
def architecture():
    b = []
    b.append(rect(20, 95, 1360, 830, "#fafbfc", LINE, dash="8 6"))
    b.append(text(40, 124, "Machine hôte (Mac) · dossier du projet", 15, MUTED, "700"))

    # Fichiers de l'hôte (colonne gauche)
    b.append(card(40, 145, 290, 95, ".env", ["mots de passe (jamais sur GitHub)", "→ variables des 3 services"],
                  RED, RED_BG))
    b.append(card(40, 260, 290, 90, "mongo-init/", ["01-create-users.js", "monté en lecture seule (:ro)"], AMBER, AMBER_BG))
    b.append(card(40, 370, 290, 95, "MongoDB Compass", ["ou mongosh, depuis le Mac", "→ localhost:27017"], INK, "#ffffff"))
    b.append(card(40, 745, 290, 80, "data/", ["healthcare_dataset.csv"], AMBER, AMBER_BG))

    # Réseau Docker
    NX, NY, NW, NH = 360, 140, 815, 540
    b.append(rect(NX, NY, NW, NH, "#f3f7fc", BLUE, dash="10 6"))
    b.append(text(NX + 18, NY + 28, "Réseau Docker : medical_network", 16, BLUE, "700"))

    b.append(card(390, 185, 360, 420, "mongodb", [
        "image : mongo:7.0", "authentification activée", "(MONGO_INITDB_ROOT_*)", "",
        "1er démarrage : exécute", "01-create-users.js", "→ rôles + utilisateurs", "",
        "healthcheck : ping / 5 s", "restart : unless-stopped", "port 27017 publié"], GREEN, GREEN_BG))
    b.append(card(885, 185, 270, 190, "migration", [
        "build : Dockerfile", "1. pytest test_transform.py", "2. python src/migrate.py",
        "user : migration_user", "(readWrite)"], BLUE, BLUE_BG))
    b.append(card(885, 435, 270, 170, "tests", [
        "build : Dockerfile", "pytest test_database.py", "user : analyst_user",
        "(read, lecture seule)"], BLUE, BLUE_BG))
    b.append(text(600, 655, "Ordre : mongodb « healthy » → migration (code 0) → tests", 14, BLUE, "700"))

    # Flux principaux
    b.append(line([(885, 245), (752, 245)]))
    b.append(text(818, 236, "écrit", 13, INK, "700", anchor="middle"))
    b.append(line([(885, 520), (752, 520)]))
    b.append(text(818, 511, "lit", 13, INK, "700", anchor="middle"))
    b.append(line([(330, 305), (388, 305)]))
    b.append(line([(330, 418), (388, 418)]))

    # Export (colonne droite)
    b.append(card(1205, 185, 160, 120, "data/export/", ["admissions_", "export.json"], AMBER, AMBER_BG))
    b.append(line([(1155, 245), (1203, 245)]))

    # Volumes
    b.append(text(390, 725, "Volumes nommés", 15, MUTED, "700"))
    b.append(cylinder(420, 740, 300, 100, "mongo_data", "→ mongodb:/data/db", GREEN, GREEN_BG))
    b.append(line([(570, 605), (570, 738)], color=GREEN, marker="arrg", dash="6 4"))
    b.append(cylinder(870, 740, 300, 100, "csv_data", "./data → /data/csv:ro", AMBER, AMBER_BG))
    b.append(line([(1020, 738), (1020, 607)], color=AMBER, marker="arrg", dash="6 4"))
    b.append(line([(1170, 790), (1190, 790), (1190, 340), (1157, 340)], color=AMBER, marker="arrg", dash="6 4"))
    b.append(line([(185, 825), (185, 885), (1020, 885), (1020, 842)], color=AMBER, marker="arrg", dash="6 4"))
    b.append(text(600, 908, "le dossier ./data est monté dans le volume csv_data", 13, MUTED, anchor="middle",
                  style="italic"))
    b.append(text(570, 864, "conservé après docker compose down", 13, MUTED, anchor="middle", style="italic"))
    return svg(1400, 945, "\n".join(b), "Architecture Docker",
               "docker compose up --build : 3 services, 2 volumes nommés, 1 réseau nommé")


# ---------------------------------------------------------------- 3. rôles et utilisateurs
def roles():
    b = []
    cols = ["Lire", "Ajouter", "Modifier", "Supprimer", "Créer index", "Gérer users"]
    rows = [
        ("admin", "root", "intégré", "administration", [1, 1, 1, 1, 1, 1], RED),
        ("migration_user", "readWrite", "intégré", "service migration", [1, 1, 1, 1, 1, 0], BLUE),
        ("soignant_user", "editeurDossiers", "personnalisé", "personnel soignant", [1, 1, 1, 0, 0, 0], AMBER),
        ("analyst_user", "read", "intégré", "service tests, analyses", [1, 0, 0, 0, 0, 0], GREEN),
    ]
    X, Y, NAME_W, ROLE_W, USE_W, CW, RH = 40, 110, 230, 230, 230, 110, 78
    total = NAME_W + ROLE_W + USE_W + CW * len(cols)
    b.append(rect(X, Y, total, 56, INK, INK, r=10))
    heads = [("Utilisateur", X + 18), ("Rôle MongoDB", X + NAME_W + 18), ("Utilisé par", X + NAME_W + ROLE_W + 18)]
    for h, hx in heads:
        b.append(text(hx, Y + 35, h, 16, "#ffffff", "700"))
    cx0 = X + NAME_W + ROLE_W + USE_W
    for i, c in enumerate(cols):
        b.append(text(cx0 + CW * i + CW / 2, Y + 35, c, 15, "#ffffff", "700", anchor="middle"))
    for r, (user, role, kind, use, perms, color) in enumerate(rows):
        y = Y + 56 + r * RH
        b.append(rect(X, y, total, RH, "#ffffff" if r % 2 else GRAY_BG, LINE, r=0, sw=1))
        b.append(f'<rect x="{X}" y="{y}" width="8" height="{RH}" fill="{color}"/>')
        b.append(text(X + 24, y + 34, user, 17, INK, "700", MONO))
        b.append(text(X + 24, y + 58, "base d'auth. : " + ("admin" if user == "admin" else "healthcare"), 12, MUTED))
        b.append(text(X + NAME_W + 18, y + 34, role, 17, color, "700", MONO))
        b.append(text(X + NAME_W + 18, y + 58, "rôle " + kind, 12, MUTED))
        b.append(text(X + NAME_W + ROLE_W + 18, y + 45, use, 15))
        for i, ok in enumerate(perms):
            cx, cy = cx0 + CW * i + CW / 2, y + RH / 2
            if ok:
                b.append(f'<circle cx="{cx}" cy="{cy}" r="17" fill="{GREEN_BG}" stroke="{GREEN}" stroke-width="2"/>')
                b.append(f'<path d="M{cx - 8},{cy} L{cx - 2},{cy + 7} L{cx + 9},{cy - 7}" fill="none" '
                         f'stroke="{GREEN}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')
            else:
                b.append(f'<circle cx="{cx}" cy="{cy}" r="17" fill="{RED_BG}" stroke="{RED}" stroke-width="2"/>')
                b.append(f'<path d="M{cx - 7},{cy - 7} L{cx + 7},{cy + 7} M{cx + 7},{cy - 7} L{cx - 7},{cy + 7}" '
                         f'stroke="{RED}" stroke-width="3.5" stroke-linecap="round"/>')

    y = Y + 56 + 4 * RH + 40
    w3 = (total - 40) / 3
    b.append(card(X, y, w3, 160, "Moindre privilège", [
        "Chacun n'a que les droits", "nécessaires à sa mission.", "Un mot de passe volé limite",
        "donc les dégâts possibles."], INK, GRAY_BG))
    b.append(card(X + w3 + 20, y, w3, 160, "Rôle personnalisé", [
        "editeurDossiers sur admissions :", "actions find, insert, update.", "L'action remove est absente :",
        "le soignant ne supprime rien."], AMBER, AMBER_BG))
    b.append(card(X + 2 * (w3 + 20), y, w3, 160, "Mots de passe hachés", [
        "SCRAM-SHA-256 : sel aléatoire", "+ 15 000 itérations.", "Seuls salt, storedKey et serverKey",
        "sont stockés, jamais le mot de passe."], GREEN, GREEN_BG))
    b.append(text(X, y + 200, "Vérifié : connexion sans mot de passe → « requires authentication » · "
                  "analyst_user insertOne → « not authorized » · soignant_user deleteOne → « not authorized »",
                  14, MUTED, style="italic"))
    return svg(1400, Y + 56 + 4 * RH + 275, "\n".join(b), "Utilisateurs et rôles",
               "Authentification activée · 4 utilisateurs, du plus puissant au plus restreint")


# ---------------------------------------------------------------- 4. flux de migration
def flux():
    b = []
    W, H, G, X0 = 300, 185, 40, 50
    xs = [X0 + i * (W + G) for i in range(4)]
    R1, R2 = 115, 395

    def step(x, y, num, title, lines, color, bg):
        out = [rect(x, y, W, H, bg, color)]
        if num:
            out.append(f'<circle cx="{x + 30}" cy="{y + 32}" r="17" fill="{color}"/>')
            out.append(text(x + 30, y + 38, num, 17, "#ffffff", "700", anchor="middle"))
            out.append(text(x + 58, y + 39, title, 18, color, "700"))
        else:
            out.append(text(x + 18, y + 39, title, 18, color, "700"))
        for i, s in enumerate(lines):
            out.append(text(x + 18, y + 74 + i * 24, s, 14))
        return "\n".join(out)

    b.append(step(xs[0], R1, "", "healthcare_dataset.csv", [
        "55 500 lignes, 15 colonnes", "lu en texte (dtype=str)", "via le volume csv_data"], MUTED, GRAY_BG))
    b.append(step(xs[1], R1, "", "Tests unitaires", [
        "pytest test_transform.py", "6 tests sur un mini CSV", "échec → migration annulée"], AMBER, AMBER_BG))
    b.append(step(xs[2], R1, "1", "Contrôle AVANT", [
        "15 colonnes présentes ?", "valeurs manquantes : 0", "doublons : 534"], BLUE, BLUE_BG))
    b.append(step(xs[3], R1, "2", "Nettoyage, typage", [
        "espaces, noms « Prénom Nom »", "int / double (2 déc.) / date", "– 534 doublons → 54 966"], BLUE, BLUE_BG))
    b.append(step(xs[3], R2, "3", "Insertion par lots", [
        "collection vidée (rejouable)", "insert_many × 11 lots de 5 000", "user : migration_user"], GREEN, GREEN_BG))
    b.append(step(xs[2], R2, "4", "Création des index", [
        "patient.name", "medical_condition", "admission.date, .hospital"], GREEN, GREEN_BG))
    b.append(step(xs[1], R2, "5", "Contrôle APRÈS", [
        "54 966 documents ?", "champs obligatoires ($exists)", "types BSON ($type)"], GREEN, GREEN_BG))
    b.append(step(xs[0], R2, "6", "Export JSON", [
        "data/export/", "admissions_export.json", "sauvegarde lisible (23 Mo)"], AMBER, AMBER_BG))

    my1, my2 = R1 + H / 2, R2 + H / 2
    for i in range(3):
        b.append(line([(xs[i] + W, my1), (xs[i + 1] - 3, my1)]))
        b.append(line([(xs[i + 1], my2), (xs[i] + W + 3, my2)]))
    b.append(line([(xs[3] + W / 2, R1 + H), (xs[3] + W / 2, R2 - 3)]))
    b.append(text(xs[3] + W / 2 + 12, R1 + H + 58, "connexion (10 essais)", 13, MUTED, style="italic"))

    R3 = 680
    b.append(line([(xs[0] + W / 2, R2 + H), (xs[0] + W / 2, R3 - 3)]))
    b.append(text(xs[0] + W / 2 + 12, R2 + H + 58, "code retour 0", 13, MUTED, style="italic"))
    full = 4 * W + 3 * G
    b.append(rect(X0, R3, full * 0.62, 130, BLUE_BG, BLUE))
    b.append(text(X0 + 18, R3 + 38, "Service tests : pytest test_database.py (analyst_user, lecture seule)",
                  18, BLUE, "700"))
    b.append(text(X0 + 18, R3 + 72, "nombre de documents · aucun doublon · types BSON · 4 index présents", 15))
    b.append(text(X0 + 18, R3 + 98, "· écriture refusée à l'analyste  →  5 passed", 15))
    ex = X0 + full * 0.62 + 30
    b.append(rect(ex, R3, full - (ex - X0), 130, RED_BG, RED))
    b.append(text(ex + 18, R3 + 38, "En cas d'erreur à n'importe quelle étape", 17, RED, "700"))
    b.append(text(ex + 18, R3 + 72, "log [ERROR] + sys.exit(1)", 15, INK, family=MONO))
    b.append(text(ex + 18, R3 + 98, "→ le service tests ne démarre pas", 15))
    return svg(1400, 850, "\n".join(b), "Flux de la migration",
               "Ce qui se passe quand on lance docker compose up --build (service migration, puis service tests)")


os.makedirs(OUT, exist_ok=True)
for name, fn in [("schema_base", schema_base), ("architecture_docker", architecture),
                 ("roles_utilisateurs", roles), ("flux_migration", flux)]:
    with open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8") as f:
        f.write(fn())
    print("écrit", name + ".svg")
