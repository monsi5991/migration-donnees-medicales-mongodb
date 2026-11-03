# Recherches : déployer MongoDB sur AWS

*Projet 5 – Migration des données médicales vers MongoDB · Simon Sagna · novembre 2026*

Le projet tourne aujourd'hui en local avec Docker. Le client a des problèmes de **scalabilité** : la suite logique est d'héberger la base dans le cloud. Ce document compare les options proposées par AWS pour MongoDB.

> Prix relevés en novembre 2026, région **US East (N. Virginia)**, hors taxes. Les régions européennes (Paris, Irlande, Francfort) sont en général un peu plus chères. Les tarifs évoluent : vérifier avec le [calculateur AWS](https://calculator.aws/) avant toute décision.

---

## 1. Point de vocabulaire : « Amazon RDS pour MongoDB » n'existe pas

**Amazon RDS** (Relational Database Service) ne gère que des bases **relationnelles** : MySQL, PostgreSQL, MariaDB, Oracle, SQL Server, Db2, ainsi qu'Aurora. Pour MongoDB, AWS propose un service distinct : **Amazon DocumentDB (with MongoDB compatibility)**.

---

## 2. Les 4 façons d'avoir MongoDB sur AWS

### 2.1 Amazon DocumentDB : le service géré d'AWS

**Principe.** Base de données documents **gérée par AWS**, qui « parle » le protocole MongoDB. Les applications, les pilotes (pymongo) et les outils (mongosh, Compass) fonctionnent avec peu ou pas de modifications. Ce n'est **pas** le moteur MongoDB : c'est un moteur AWS compatible avec son API.

**Compatibilité.** API MongoDB **4.0, 5.0 et 8.0**. Avec DocumentDB 8.0, les applications écrites pour les API 6.0 et 7.0 sont aussi prises en charge. Toutes les fonctionnalités de MongoDB ne sont pas disponibles : la liste des API supportées est à vérifier avant de migrer.

**Architecture.**
- un **cluster** = 1 instance principale (lecture/écriture) + jusqu'à 15 réplicas en lecture ;
- le **stockage est séparé du calcul** : 6 copies des données sur 3 zones de disponibilité, il grandit automatiquement (jusqu'à 128 Tio, 256 Tio en 8.0) ;
- en cas de panne de l'instance principale, un réplica prend le relais automatiquement ;
- option **Elastic Clusters** pour le partitionnement horizontal (*sharding*) de très gros volumes.

**Tarifs** (à la demande) :

| Élément | Prix |
|---|---|
| Instance `db.t3.medium` (2 vCPU, 4 Go) | ≈ 0,078 $/h, soit ≈ 57 $/mois |
| Instance `db.r5.large` (2 vCPU, 16 Go) | 0,277 $/h, soit ≈ 202 $/mois |
| Stockage (cluster *Standard*) | 0,10 $/Go/mois |
| Entrées/sorties (cluster *Standard*) | 0,20 $ par million |
| Cluster *I/O-Optimized* | pas de frais d'E/S, stockage à 0,30 $/Go/mois, instances ≈ 10 % plus chères |
| Sauvegardes | gratuites jusqu'à 100 % de la taille du cluster |
| Essai gratuit (30 jours) | 750 h de `db.t3.medium`, 30 millions d'E/S, 5 Go de stockage, 5 Go de sauvegarde |

### 2.2 MongoDB Atlas sur AWS : le service géré de MongoDB

**Principe.** Le service cloud de l'éditeur MongoDB. On choisit AWS comme fournisseur et une région (par exemple Paris). C'est le **vrai moteur MongoDB**, toujours dans la dernière version, avec toutes ses fonctionnalités. Il est aussi disponible sur l'AWS Marketplace, et la facture peut alors passer par le compte AWS.

| Offre | Prix | Ressources |
|---|---|---|
| **M0 (Free)** | gratuit | 512 Mo, ressources partagées |
| **Flex** | 0,011 $/h, plafonné à 30 $/mois | 5 Go, ressources partagées |
| **M10 (Dedicated)** | 0,08 $/h, à partir de ≈ 57 $/mois | 2 vCPU, 2 Go de RAM, 10 à 128 Go |

Inclus : réplication sur 3 nœuds, sauvegardes, supervision, chiffrement, recherche plein texte (*Atlas Search*) et vectorielle.

### 2.3 MongoDB installé soi-même sur Amazon EC2

**Principe.** On loue une ou plusieurs machines virtuelles (EC2) et on y installe MongoDB, directement ou avec Docker, comme dans ce projet.

- **Avantage** : contrôle total (version, configuration) et coût de calcul le plus bas. Une `t3.medium` coûte environ 0,04 $/h (≈ 30 $/mois), plus le disque EBS.
- **Inconvénient** : tout est à notre charge : mises à jour, sécurité, sauvegardes, réplication (*replica set* sur 3 machines pour la haute disponibilité), supervision.

### 2.4 Conteneurs sur Amazon ECS (Fargate) ou EKS

**Principe.** Reprendre directement nos images Docker. **ECS** est l'orchestrateur de conteneurs d'AWS, et **Fargate** le fait tourner sans serveur à gérer. **EKS** est la version Kubernetes.

- **Pour le conteneur de migration** : très adapté. C'est une tâche ponctuelle (elle démarre, migre, s'arrête), qu'on peut déclencher à la demande ou selon un planning.
- **Pour MongoDB lui-même** : déconseillé en production. Une base de données a besoin d'un stockage persistant et performant, et d'une gestion fine de la réplication. Mieux vaut un service géré (2.1 ou 2.2).

---

## 3. Comparaison

| Critère | DocumentDB | Atlas sur AWS | MongoDB sur EC2 | MongoDB sur ECS |
|---|---|---|---|---|
| Gestion (mises à jour, pannes) | AWS | MongoDB Inc. | **nous** | **nous** |
| Moteur | compatible MongoDB | **vrai MongoDB** | vrai MongoDB | vrai MongoDB |
| Compatibilité avec notre code (pymongo, `$group`, `$type`, rôles) | bonne (à tester) | totale | totale | totale |
| Haute disponibilité | automatique (3 zones) | automatique (3 nœuds) | à construire | à construire |
| Sauvegardes | automatiques, restauration à la seconde près, jusqu'à 35 jours | automatiques | à scripter (`mongodump`, snapshots EBS) | à scripter |
| Mise à l'échelle | réplicas de lecture, Elastic Clusters | changement de palier, sharding | manuelle | manuelle |
| Intégration AWS (IAM, VPC, KMS, CloudWatch) | **native** | via VPC peering / PrivateLink | native | native |
| Coût minimal d'un environnement | ≈ 57 $/mois (essai gratuit 30 j) | **0 $** (M0) | ≈ 30 $/mois | variable |
| Effort d'exploitation | faible | faible | **élevé** | **élevé** |

---

## 4. Ce qu'il faudrait pour déployer ce projet sur AWS

```
 S3 (CSV)  ──►  ECS Fargate : tâche « migration » (notre image Docker)  ──►  DocumentDB ou Atlas
                          │                                                        │
              Secrets Manager (mots de passe)                       sauvegardes automatiques
                          │                                                        │
                    CloudWatch (logs)                              VPC privé, chiffrement KMS
```

| Besoin | Service AWS | Remplace, dans le projet actuel |
|---|---|---|
| stocker le CSV | **Amazon S3** | le volume `csv_data` |
| stocker les images Docker | **Amazon ECR** | les images locales |
| lancer la migration | **ECS Fargate** (tâche ponctuelle) | le service `migration` du docker-compose |
| base de données | **DocumentDB** ou **Atlas** | le service `mongodb` |
| mots de passe | **AWS Secrets Manager** | le fichier `.env` |
| journaux | **Amazon CloudWatch Logs** | `docker compose logs` |
| réseau isolé | **VPC** avec sous-réseaux privés | le réseau `medical_network` |
| droits d'accès AWS | **IAM** | (en plus des rôles MongoDB) |
| migration depuis une base existante | **AWS DMS** (Database Migration Service) | – |

**Spécificité des données de santé.** En France, l'hébergement de données de santé doit être confié à un hébergeur certifié **HDS** (Hébergeur de Données de Santé), en plus du respect du **RGPD**. Il faut choisir une région européenne (par exemple **Paris, eu-west-3**), activer le chiffrement au repos (KMS) et en transit (TLS), et vérifier la certification HDS du service retenu avant toute mise en production.

---

## 5. Recommandation

| Contexte | Choix | Pourquoi |
|---|---|---|
| **Démonstration / soutenance** | **Atlas M0** (gratuit) | nos données (54 966 documents, quelques dizaines de Mo) tiennent dans 512 Mo ; vrai MongoDB, donc aucun changement de code |
| **Production chez le client, tout sur AWS** | **Amazon DocumentDB** (`db.t4g.medium` ou `db.t3.medium` au départ) + migration sur **ECS Fargate** | service géré, haute disponibilité, sauvegardes automatiques, intégration native IAM/VPC/KMS/CloudWatch, montée en charge par réplicas |
| **Besoin de toutes les fonctionnalités MongoDB** | **Atlas M10** (ou plus) sur AWS | même prix d'entrée que DocumentDB, compatibilité totale |

À éviter pour ce client : MongoDB installé à la main sur EC2 ou ECS. L'effort d'exploitation (sécurité, sauvegardes, réplication) est élevé, et le gain financier est faible face à un service géré.

**Avant de choisir DocumentDB**, il faudrait vérifier que les opérations utilisées par le projet sont supportées : `insert_many`, index simples, `$group`/`$avg`, `$type`, `$exists`, rôles personnalisés.

---

## Sources

- [Amazon DocumentDB – tarifs](https://aws.amazon.com/documentdb/pricing/)
- [Amazon DocumentDB – compatibilité avec MongoDB](https://docs.aws.amazon.com/documentdb/latest/developerguide/compatibility.html)
- [AWS Database Blog – optimiser les coûts d'Amazon DocumentDB](https://aws.amazon.com/blogs/database/optimizing-for-cost-with-amazon-documentdb-with-mongodb-compatibility/) (prix d'une instance de 4 Go)
- [MongoDB Atlas – tarifs](https://www.mongodb.com/pricing)
- [Calculateur de prix AWS](https://calculator.aws/)
