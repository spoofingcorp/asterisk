# **Asterisk 2025 : Administration, Engineering & Architecture**

**Support de Cours et Laboratoire Pratique - Édition Expert (Validée, Corrigée & Augmentée)**

Ce document sert de référence technique exhaustive pour les ingénieurs télécoms, administrateurs système et architectes VoIP souhaitant déployer, sécuriser et maintenir une infrastructure de téléphonie critique.

* **Version Asterisk cible** : 20 LTS (Production Critique) ou 22 (R&D)
* **OS Recommandé** : Debian 12 "Bookworm" (Hardened)

## **TABLE DES MATIÈRES DÉTAILLÉE**

1. **Architecture et Écosystème 2025**
* 1.1 Cycle de vie et choix stratégique : LTS vs Standard
* 1.2 PJSIP sous le capot : Threading, Sorcery et Objets
* 1.3 Sécurité Défensive Avancée : Fail2Ban, ACLs, TLS/SRTP et GeoIP


2. **Stratégie de Production & DevOps**
* 2.1 Modularité et Infrastructure as Code (Git, Ansible)
* 2.2 Gestion du "Zero Downtime" et Persistance
* 2.3 Optimisation Système : Kernel, Ulimit et Priorité Temps Réel


3. **Installation et Préparation Système**
* 3.1 Dépendances, Paquets et Compilation sur mesure
* 3.2 Configuration Réseau, Pare-feu et QoS (DSCP)


4. **Laboratoire : Configuration des Services (Core)**
* 4.1 Endpoints PJSIP : Codecs, NAT Traversal (ICE/STUN) et Direct Media
* 4.2 Musique d'Attente (MoH) : Impact CPU, Transcodage et Streaming
* 4.3 Call Center : Stratégies ACD, Pénalités et Rapports
* 4.4 Trunks SIP : Interopérabilité, Timers et SBC Distribués


5. **Laboratoire : Engineering du Dialplan**
* 5.1 Pattern Matching Avancé et Variables de Canal
* 5.2 Expérience Appelant : Pré-décroché vs Early Media (180/183)
* 5.3 IVR Dynamique : Arborescence, Timeouts et Retry
* 5.4 Manipulation d'Identité (CallerID, PAI, RPID) et Conformité


6. **Interconnexion Site-à-Site (IAX2)**
* 6.1 Avantages protocolaires : Trunking et Overhead
* 6.2 Configuration du Tunnel Chiffré


7. **Maintenance, Troubleshooting et Forensic**
* 7.1 Analyse SIP temps réel (sngrep) et interprétation des codes
* 7.2 Analyse RTP Forensic (Wireshark, Jitter Buffer, RTCP)



---

## **1. ARCHITECTURE ET ÉCOSYSTÈME 2025**

### **1.1 Les Versions Actuelles : Faire le bon choix stratégique**

Le choix de la version d'Asterisk définit votre politique de maintenance sur le long terme.

* **Asterisk 20 LTS (Long Term Support)** : C'est le socle industriel incontournable pour les environnements de production. Une version LTS garantit :
* **Support de 5 ans** (jusqu'en 2027) : Correctifs de sécurité critiques sans changement de fonctionnalité.
* **Stabilité des API/ABI** : Vos scripts AGI (Python/PHP), vos modules binaires compilés ou vos connecteurs de base de données (ODBC/Realtime) ne casseront pas lors d'une mise à jour mineure.
* **Focus** : Idéal pour les opérateurs, centres d'appels et entreprises cherchant le "Set and Forget".


* **Asterisk 22 (Standard)** : Sortie fin 2024, cette version est réservée à la R&D. Elle introduit des ruptures technologiques (support étendu WebRTC, codecs vidéo 4K/VR, nouvelles API REST ARI). Son cycle de vie court (1 an) impose des migrations fréquentes, incompatibles avec une SLA de production élevée (99.999%).

### **1.2 PJSIP : Le Standard Unique**

L'ancien pilote chan_sip (monolithique, single-threaded) a été définitivement retiré. **PJSIP** (basé sur la librairie PJPROJECT) offre une architecture modulaire :

* **Architecture Asynchrone** : PJSIP utilise un pool de threads dynamique (distributor). Cela permet de traiter des dizaines de milliers de sessions simultanées sans bloquer le cœur du système ("deadlocks"), contrairement à chan_sip qui s'effondrait sous la charge.
* **Abstraction "Sorcery"** : La configuration est découpée en objets logiques indépendants :
* **Endpoint** : Profil technique (Codecs, Timers, DTMF, Contexte).
* **AOR (Address of Record)** : Localisation réseau. Permet le **support multi-device** (un compte = plusieurs contacts : téléphone fixe + softphone mobile sonnant simultanément).
* **Auth** : Identifiants de sécurité.
* **Identify** : Méthode de reconnaissance pour les Trunks IP (matching par adresse IP source au lieu du username).



### **1.3 Sécurité Défensive et Bonnes Pratiques**

Un IPBX exposé est attaqué dans les minutes qui suivent sa mise en ligne (Toll Fraud, SIP Scanning).

* **Fail2Ban (IDS)** : Première ligne de défense. Il scanne `/var/log/asterisk/security`, détecte les motifs d'attaque (SIP 403/401 répétitifs, tentatives sur des users inexistants) et bannit dynamiquement les IP via iptables/nftables.
* *Conseil Pro* : Configurez une bantime incrémentale (1h, puis 24h, puis 1 semaine).


* **ACL (Access Control Lists)** : Restriction applicative dans `pjsip.conf`. Utilisez permit/deny pour whitelister strictement vos sous-réseaux LAN et les IP de signalisation de votre opérateur. Le reste du monde doit être bloqué.
* **Chiffrement (TLS & SRTP)** : En 2025, le SIP en clair (UDP/5060) est une faille.
* **TLS** : Chiffre la signalisation (qui appelle qui).
* **SRTP** : Chiffre la voix. Indispensable pour éviter l'écoute clandestine sur des réseaux non sûrs (WiFi public, Internet).



---

## **2. STRATÉGIE DE PRODUCTION & DEVOPS**

### **2.1 Modularité et Infrastructure as Code**

Gérer un fichier `pjsip.conf` monolithique de 5000 lignes est une erreur critique.

* **Inclusions (#include)** : Segmentez vos fichiers par fonction (`pjsip_users.conf`, `pjsip_trunks.conf`, `pjsip_transports.conf`). Cela permet de :
* Isoler les responsabilités.
* Générer automatiquement la liste des utilisateurs via un script (Python/Ansible) sans risquer d'écraser la configuration du Trunk opérateur.


* **Versioning (Git)** : Tout le dossier `/etc/asterisk` doit être sous Git.
* Permet l'audit : "Qui a changé le mot de passe du Trunk hier à 18h ?"
* Permet le Rollback immédiat (`git revert`) en cas de configuration défectueuse.



### **2.2 Reload à chaud : Le "Zero Downtime"**

* **core restart (DANGER)** : Tue le processus. Coupe brutalement la signalisation et les flux audio (RTP). À n'utiliser que pour une mise à jour binaire ou un changement de module kernel.
* **pjsip reload** : Recharge uniquement la configuration des objets PJSIP. Les sessions SIP établies (appels en cours) restent en mémoire et ne sont pas affectées.
* **dialplan reload** : Met à jour la logique de routage. Les nouveaux appels prennent le nouveau chemin, les anciens terminent leur cycle.
* **module reload res_musiconhold.so** : Permet de mettre à jour les playlists musicales sans toucher au cœur téléphonique.

### **2.3 Optimisation Système**

Pour supporter la charge :

* **Ulimit** : Asterisk ouvre beaucoup de descripteurs de fichiers (sockets + fichiers audio). Augmentez la limite dans systemd (`LimitNOFILE=100000`).
* **Priorité Temps Réel** : Lancez Asterisk avec une priorité CPU élevée (`nice -n -20`) pour éviter que le traitement audio ne soit retardé par d'autres processus (logs, backups).

---

## **3. INSTALLATION ET PRÉPARATION SYSTÈME**

### **3.1 Installation sur Debian 12**

Privilégiez les paquets officiels pour la stabilité, sauf besoin spécifique de modules tiers.

```bash
# 1. Mise à jour et durcissement
sudo apt update && sudo apt upgrade -y

# 2. Installation Core & Sons
# asterisk-core-sounds-fr-g722 : Sons systèmes en Haute Définition (Wideband).
# asterisk-moh-opsound-wav : Musique libre de droits pour éviter les problèmes légaux.
sudo apt install asterisk asterisk-core-sounds-fr asterisk-core-sounds-fr-g722 asterisk-moh-opsound-wav -y

# 3. Outils d'analyse "Forensic"
# sngrep : Interface ncurses pour visualiser le SIP en temps réel (indispensable).
# tcpdump : Pour capturer le trafic brut et l'analyser dans Wireshark.
# fail2ban : Pour la protection active.
sudo apt install sngrep tcpdump fail2ban htop -y

# 4. Activation
sudo systemctl enable asterisk
sudo systemctl start asterisk

```

### **3.2 Configuration Réseau et Pare-feu**

La VoIP traverse deux plans distincts :

* **Control Plane (SIP - UDP/TCP 5060)** : Signalisation. Cible des attaques. À restreindre aux IP de confiance (Trunk, VPN, LAN).
* **Data Plane (RTP - UDP 10000-20000)** : Audio. Doit être ouvert largement (0.0.0.0/0) en UDP.
* *Pourquoi ?* L'audio vient souvent de Media Gateways (SBC) de l'opérateur dont les IP sont différentes de l'IP de signalisation et peuvent changer dynamiquement.


* **QoS (DSCP)** : Marquez les paquets sortants avec DSCP 46 (EF - Expedited Forwarding) pour qu'ils soient prioritaires sur les routeurs/switchs de l'entreprise.

---

## **4. LABORATOIRE : CONFIGURATION DES SERVICES (CORE)**

### **Préparation "Greenfield"**

```bash
cd /etc/asterisk
sudo mkdir -p backups/original_conf
sudo mv pjsip.conf extensions.conf queues.conf voicemail.conf musiconhold.conf backups/original_conf/
sudo touch pjsip.conf pjsip_users.conf pjsip_trunk.conf extensions.conf extensions_custom.conf queues.conf voicemail.conf musiconhold.conf

```

### **4.1 Endpoints PJSIP : Paramètres avancés**

**pjsip.conf (Infrastructure) :**

```ini
[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0
; local_net : CRITIQUE pour le NAT. Indique à Asterisk : "Si l'IP cible est dans ce réseau,
; ne modifie pas les headers SIP, sinon, réécris l'IP publique".
local_net=192.168.1.0/24

#include pjsip_users.conf
#include pjsip_trunk.conf

```

**pjsip_users.conf (Utilisateurs) :**

```ini
[user-template](!)
type=endpoint
context=from-internal
disallow=all
; Ordre des codecs : HD (G722) > Standard Europe (ALAW/PCMA) > US (ULAW/PCMU)
allow=g722,alaw,ulaw
; direct_media=no : Asterisk reste "Man-in-the-Middle" pour l'audio.
; Avantages : Enregistrement des appels possible, écoute discrète, isolation des VLANs voix,
; résout 90% des problèmes de "One Way Audio" liés au NAT.
direct_media=no
; force_rport=yes : Force la réponse sur le port source du paquet reçu (contournement NAT client).
force_rport=yes
; rewrite_contact=yes : Réécrit l'IP du header Contact avec l'IP source du paquet IP (vital pour les utilisateurs nomades).
rewrite_contact=yes
mailboxes=${ENDPOINT}@default

[6001](user-template)
auth=auth6001
aors=6001
[auth6001]
type=auth
auth_type=password
password=ComplexPassAlice_2025!
username=6001
[6001]
type=aor
max_contacts=2 ; Permet à Alice d'avoir PC et Mobile connectés en même temps.

[6002](user-template)
auth=auth6002
aors=6002
[auth6002]
type=auth
auth_type=password
password=ComplexPassBob_2025!
username=6002
[6002]
type=aor
max_contacts=1

```

#### **🛑 MISE EN SITUATION : TEST TRANSCODAGE**

**Objectif :** Valider la capacité de transcodage (coûteuse en CPU).

1. **Config :** Forcez un softphone en GSM (si dispo) et l'autre en G722.
2. **Appel :** Lancez l'appel.
3. **Observation :** `core show channels` affichera les formats. Le serveur décode le GSM vers PCM, puis ré-encode en G722. C'est transparent pour l'utilisateur mais charge le CPU.

### **4.2 Musique d'Attente (MoH)**

Le transcodage MP3 -> SLIN -> ALAW consomme énormément de CPU. En production, **convertissez vos fichiers en WAV (8kHz, 16bit, Mono)** ou directement en .alaw pour que le serveur n'ait qu'à copier les octets vers le réseau sans traitement.

```ini
[default]
mode=files
directory=/var/lib/asterisk/sounds/moh
sort=random

[commercial]
mode=files
directory=/var/lib/asterisk/sounds/custom_marketing
sort=alpha ; Lecture séquentielle (Pub 1, Pub 2...)

```

*Application : `asterisk -rx "moh reload"*`

### **4.3 Call Center : Stratégies ACD**

**queues.conf :**

```ini
[support-queue]
musicclass=default
; strategy=rrmemory : Round Robin Memory. Distribue équitablement en se souvenant du dernier agent
; qui a pris un appel, et commence par le suivant.
strategy=rrmemory
joinempty=no         ; Interdit d'entrer si aucun agent connecté/disponible.
leavewhenempty=yes   ; Éjecte les appelants si le dernier agent se déconnecte.
timeout=20           ; Temps de sonnerie par agent.
retry=5              ; Temps de pause avant de réessayer un autre agent.
wrapuptime=15        ; Temps de repos (administratif) pour l'agent après un appel avant de refaire sonner.
member => PJSIP/6001
member => PJSIP/6002

```

#### **🛑 MISE EN SITUATION : TEST QUEUE & ANALYTICS**

1. **Action :** Bob (6002) refuse l'appel.
2. **Appel :** Appelez le 800.
3. **Observation :** `queue show support-queue`. L'appelant est en attente.
4. **Logs :** Vérifiez `/var/log/asterisk/queue_log`. Chaque événement (ENTERQUEUE, CONNECT, ABANDON) est tracé pour les statistiques (SLA, Temps moyen d'attente).

### **4.4 Interconnexion Trunk SIP**

La gestion des **Timers** et du **Keepalive** est vitale pour détecter une coupure de lien opérateur.

**pjsip_trunk.conf :**

```ini
[trunk-provider]
type=registration
outbound_auth=auth-trunk
server_uri=sip:sip.provider.com
client_uri=sip:LOGIN@sip.provider.com
; Expiration réduite à 120s (vs 3600s défaut) pour se ré-enregistrer rapidement après une panne internet.
expiration=120

[auth-trunk]
type=auth
auth_type=password
password=PASSWORD
username=LOGIN

[trunk-provider]
type=endpoint
context=from-external    ; Point d'entrée de sécurité critique.
disallow=all
allow=ulaw,alaw          ; G.711 standard opérateur.
outbound_auth=auth-trunk
aors=trunk-provider
from_user=LOGIN          ; Force le header 'From' (Anti-spoofing opérateur).
qualify_frequency=60     ; Envoie un SIP OPTIONS toutes les 60s. Si pas de réponse, marque le trunk "Unavail".

[trunk-provider]
type=aor
contact=sip:sip.provider.com

```

---

## **5. LABORATOIRE : ENGINEERING DU DIALPLAN**

**extensions.conf (Le Squelette) :**

```ini
[general]
static=yes
writeprotect=no

[globals]
SDA_STANDARD=0188001122
TRUNK=PJSIP/trunk-provider

#include extensions_custom.conf

[from-internal]
include => local-extensions
include => internal-services
include => outbound-calls

```

**extensions_custom.conf (Logique Métier) :**

```ini
; --- Extensions Locales ---
[local-extensions]
exten => _6XXX,1,NoOp(Appel Interne de ${CALLERID(num)} vers ${EXTEN})
; Option m(default) : Joue la musique au lieu de la sonnerie (Ringing).
same => n,Dial(PJSIP/${EXTEN},30,m(default))
same => n,VoiceMail(${EXTEN}@default,u)
same => n,Hangup()

; --- Services Internes ---
[internal-services]
exten => *97,1,VoiceMailMain(${CALLERID(num)}@default)
exten => 800,1,Queue(support-queue,t)

; --- Appels Sortants ---
[outbound-calls]
; Pattern matching : 0 + 9 chiffres (Format France)
exten => _0[1-9]XXXXXXXX,1,NoOp(Appel Sortant vers ${EXTEN})
; --- Normalisation CallerID ---
; On écrase le numéro interne (6001) par le numéro public du Standard pour centraliser les retours.
same => n,Set(CALLERID(all)="Societe ABC" <${SDA_STANDARD}>)
; --- Compatibilité SIP Headers ---
; Certains opérateurs (Trunk Enterprise) exigent P-Asserted-Identity (PAI) pour la facturation.
same => n,Set(PJSIP_HEADER(add,P-Asserted-Identity)=<sip:${SDA_STANDARD}@sip.provider.com>)
same => n,Dial(${TRUNK}/${EXTEN})
same => n,Hangup()

; --- Routage Entrant (SDA) ---
[from-external]
; On matche le numéro SDA fourni par l'opérateur
exten => ${SDA_STANDARD},1,Goto(accueil-entreprise,s,1)

; --- Scénario d'Accueil ---
[accueil-entreprise]
; 1. Answer() : On décroche la ligne. OBLIGATOIRE pour jouer un IVR interactif.
; La facturation commence ici pour l'appelant.
exten => s,1,Answer()
same => n,Wait(0.5) ; Stabilisation du flux audio
same => n,Playback(welcome-message)
; 2. Dial() : On fait sonner le groupe avec musique 'commercial'
same => n,Dial(PJSIP/6001&PJSIP/6002,30,m(commercial))
; 3. Echec
same => n,VoiceMail(6001@default,u)
same => n,Hangup()

```

### **5.3 IVR Dynamique**

L'IVR (*Interactive Voice Response*) permet d'aiguiller l'appel.

```ini
[ivr-principal]
exten => s,1,Answer()
; Background() : Joue le son ET écoute les touches DTMF (Barge-in).
same => n,Background(menu-principal) ; "Tapez 1 pour le support..."
same => n,WaitExten(5)               ; Attend 5 secondes après la fin du message

exten => 1,1,Queue(support-queue)
exten => 2,1,Dial(PJSIP/6002)

exten => i,1,Playback(invalid)       ; Touche invalide
same => n,Goto(s,1)                  ; Boucle
exten => t,1,Hangup()                ; Timeout (raccroche)

```

#### **🛑 MISE EN SITUATION FINALE : VALIDATION GLOBALE**

1. **Action :** Appelez votre numéro public depuis un mobile.
2. **Vérification :**
* Entendez-vous le message d'accueil ? (Preuve que le flux RTP entrant passe le NAT).
* Entendez-vous la musique d'attente "Commercial" ?
* La qualité est-elle bonne ? (Pas de gigue/hachures).



---

## **6. INTERCONNEXION SITE-À-SITE (IAX2)**

### **6.1 Avantages protocolaires**

IAX2 (Inter-Asterisk eXchange) est supérieur au SIP pour les liens inter-sites :

* **NAT Friendly** : Un seul port **UDP 4569** pour la signalisation ET l'audio. Pas de plage RTP dynamique à ouvrir.
* **Trunking (Multiplexage)** : Si 10 appels simultanés passent, IAX2 ne génère qu'un seul en-tête IP contenant 10 payloads audio. Économie massive de bande passante (overhead réduit).

### **6.2 Configuration du Tunnel**

**iax.conf :**

```ini
[site-distant]
type=friend
host=1.2.3.4       ; IP du site distant
username=paris
secret=SuperSecretTunnel
context=from-internal ; Les appels arrivent directement dans le plan de numérotation interne.
trunk=yes          ; Active le mode multiplexage.
requirecalltoken=no
encryption=yes     ; Active le chiffrement natif (sécurité type VPN).

```

---

## **7. MAINTENANCE ET ANALYSE**

### **7.1 Analyse SIP temps réel (sngrep)**

sngrep est votre tableau de bord réseau.

* **401 Unauthorized** : Normal lors de l'enregistrement (Challenge/Response).
* **403 Forbidden** : Erreur critique (Mot de passe faux, IP bannie par Fail2Ban, ou CallerID sortant non autorisé par l'opérateur).
* **408 Request Timeout** : Le paquet part mais ne revient pas (Pare-feu bloquant ou IP destination injoignable).

### **7.2 Analyse RTP Forensic (Wireshark)**

Le SIP fonctionne (le téléphone sonne), mais l'audio est hachuré, robotique ou absent (One Way Audio) ? C'est un problème de transport RTP.

1. **Capture Serveur (Full Payload) :**
```bash
# Capture brute sur l'interface (-i any) sans tronquer les paquets (-s 0)
sudo tcpdump -i any -s 0 -w /tmp/debug_audio.pcap udp port 5060 or udp portrange 10000-20000

```


2. **Analyse Wireshark (Poste Admin) :**
* Récupérez le fichier `.pcap`.
* Menu **Téléphonie -> Appels VoIP -> Analyser -> Lire les flux**.
* **Écoute** : Vous pouvez écouter l'audio tel qu'il a été vu par la carte réseau du serveur.
* Si le son est clair ici mais mauvais au téléphone : Problème réseau local (WiFi, Switch).
* Si le son est mauvais ici (trous, glitchs) : Problème en amont (Lien opérateur, perte de paquets WAN).
