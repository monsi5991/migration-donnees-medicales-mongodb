// Exécuté automatiquement par l'image mongo au PREMIER démarrage (base vide).
// Crée les rôles et utilisateurs de la base "healthcare".
// Les mots de passe viennent des variables d'environnement (fichier .env).

const dbName = process.env.MONGO_DB || "healthcare";
const db_ = db.getSiblingDB(dbName);

// Rôle personnalisé : lire, ajouter et modifier les séjours, mais jamais supprimer.
db_.createRole({
  role: "editeurDossiers",
  privileges: [
    { resource: { db: dbName, collection: "admissions" }, actions: ["find", "insert", "update"] }
  ],
  roles: []
});

// 1. Utilisateur technique de migration : lecture + écriture sur la base healthcare
db_.createUser({
  user: process.env.MONGO_MIGRATION_USER,
  pwd: process.env.MONGO_MIGRATION_PASSWORD,
  roles: [{ role: "readWrite", db: dbName }]
});

// 2. Analyste : lecture seule
db_.createUser({
  user: process.env.MONGO_ANALYST_USER,
  pwd: process.env.MONGO_ANALYST_PASSWORD,
  roles: [{ role: "read", db: dbName }]
});

// 3. Personnel soignant : rôle personnalisé (pas de suppression)
db_.createUser({
  user: process.env.MONGO_SOIGNANT_USER,
  pwd: process.env.MONGO_SOIGNANT_PASSWORD,
  roles: [{ role: "editeurDossiers", db: dbName }]
});

print("Utilisateurs et rôles créés sur la base " + dbName);
