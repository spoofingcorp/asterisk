# **Asterisk 2025 : Administration, Engineering & Architecture**

**Support de Cours et Laboratoire Pratique**

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
* 4.2 Activation du Dialplan et des Ressources (Pré-requis Test)  
* 4.3 Musique d'Attente (MoH) : Impact CPU et Théorie  
* 4.4 Gestion des Transferts, Codes Services et Diagnostic DTMF  
* 4.5 Call Center : Stratégies ACD, Pénalités et Rapports  
* 4.6 Trunks SIP : Interopérabilité, Timers et SBC Distribués  
5. **Laboratoire : Engineering Avancé du Dialplan**  
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

* **Fail2Ban (IDS)** : Première ligne de défense. Il scanne /var/log/asterisk/security, détecte les motifs d'attaque (SIP 403/401 répétitifs, tentatives sur des users inexistants) et bannit dynamiquement les IP via iptables/nftables.  
* *Conseil Pro* : Configurez une bantime incrémentale (1h, puis 24h, puis 1 semaine).  
* **ACL (Access Control Lists)** : Restriction applicative dans pjsip.conf. Utilisez permit/deny pour whitelister strictement vos sous-réseaux LAN et les IP de signalisation de votre opérateur. Le reste du monde doit être bloqué.  
* **Chiffrement (TLS & SRTP)** : En 2025, le SIP en clair (UDP/5060) est une faille.  
* **TLS** : Chiffre la signalisation (qui appelle qui).  
* **SRTP** : Chiffre la voix. Indispensable pour éviter l'écoute clandestine sur des réseaux non sûrs (WiFi public, Internet).

## **2. STRATÉGIE DE PRODUCTION & DEVOPS**

### **2.1 Modularité et Infrastructure as Code**

Gérer un fichier pjsip.conf monolithique de 5000 lignes est une erreur critique.

* **Inclusions (#include)** : Segmentez vos fichiers par fonction (pjsip_users.conf, pjsip_trunks.conf, pjsip_transports.conf). Cela permet de :  
* Isoler les responsabilités.  
* Générer automatiquement la liste des utilisateurs via un script (Python/Ansible) sans risquer d'écraser la configuration du Trunk opérateur.  
* **Versioning (Git)** : Tout le dossier /etc/asterisk doit être sous Git.  
* Permet l'audit : "Qui a changé le mot de passe du Trunk hier à 18h ?"  
* Permet le Rollback immédiat (git revert) en cas de configuration défectueuse.

### **2.2 Reload à chaud : Le "Zero Downtime"**

* **core restart (DANGER)** : Tue le processus. Coupe brutalement la signalisation et les flux audio (RTP). À n'utiliser que pour une mise à jour binaire ou un changement de module kernel.  
* **pjsip reload** : Recharge uniquement la configuration des objets PJSIP. Les sessions SIP établies (appels en cours) restent en mémoire et ne sont pas affectées.  
* **dialplan reload** : Met à jour la logique de routage. Les nouveaux appels prennent le nouveau chemin, les anciens terminent leur cycle.  
* **module reload res_musiconhold.so** : Permet de mettre à jour les playlists musicales sans toucher au cœur téléphonique.

### **2.3 Optimisation Système**

Pour supporter la charge :

* **Ulimit** : Asterisk ouvre beaucoup de descripteurs de fichiers (sockets + fichiers audio). Augmentez la limite dans systemd (LimitNOFILE=100000).  
* **Priorité Temps Réel** : Lancez Asterisk avec une priorité CPU élevée (nice -n -20) pour éviter que le traitement audio ne soit retardé par d'autres processus (logs, backups).

## **3. INSTALLATION ET PRÉPARATION SYSTÈME**

### **3.1 Installation sur Debian 12**

bash``
# 1. Passer en root (si ce n'est pas déjà fait)  
su -

# 2. Mise à jour et durcissement  
apt update && apt upgrade -y

# 3. Arrêter et désactiver le service AppArmor  
systemctl stop apparmor  
systemctl disable apparmor

# 4. (Recommandé) Désinstaller AppArmor pour éviter tout conflit futur  
apt remove apparmor -y

# 5. Installation des Dépendances de Compilation  
# Installer les outils de base pour récupérer les sources  
apt install git curl wget build-essential subversion -y

# 6. Se placer dans le répertoire des sources  
cd /usr/src

# 7. Télécharger Asterisk 22 (Dernière version courante)  
wget http://downloads.asterisk.org/pub/telephony/asterisk/asterisk-22-current.tar.gz

# 8. Décompresser l'archive  
tar xvf asterisk-22-current.tar.gz

# 9. Entrer dans le dossier  
cd asterisk-22.*/

# 10. Lancer le script de pré-requis pour Debian  
contrib/scripts/install_prereq install

# (Attendez le message "install completed successfully" avant de continuer)

# 11. Configuration de l'environnement  
./configure --with-jansson-bundled --with-pjproject-bundled

# Une fois le ./configure terminé (logo Asterisk affiché), lancez le menu :  
make menuselect

# Dans l'interface graphique (Menuselect) :   
# Add-ons : Cochez format_mp3 (si étape source MP3 réalisée).  
# Core Sound Packages : Décochez CORE-SOUNDS-EN-GSM. Cochez CORE-SOUNDS-FR-WAV et CORE-SOUNDS-FR-G722.  
# Music On Hold File Packages : Cochez MOH-OPSOUND-WAV.  
# Call Detail Recording (CDR) : DÉCOCHEZ cdr_radius.  
# Channel Event Logging (CEL) : DÉCOCHEZ cel_radius.  
# Save & Exit

# 12. Compilation et Installation  
make  
make install  
make samples  
make config  
ldconfig

# 17. Création de l'utilisateur Asterisk (Sécurité)  
groupadd asterisk  
/usr/sbin/useradd -r -d /var/lib/asterisk -g asterisk asterisk 2>/dev/null || echo "User asterisk already exists"  
usermod -aG audio,dialout asterisk

# 20. Donner les permissions sur les dossiers Asterisk  
chown -R asterisk:asterisk /etc/asterisk  
chown -R asterisk:asterisk /var/{lib,log,spool}/asterisk  
chown -R asterisk:asterisk /usr/lib/asterisk

# Configuration du service pour utiliser cet utilisateur : nano /etc/default/asterisk  
# AST_USER="asterisk"  
# AST_GROUP="asterisk"

# 21. Démarrer le service  
systemctl start asterisk  
systemctl enable asterisk  
asterisk -rvvv

# 23. Outils d'analyse "Forensic"  
apt install sngrep tcpdump fail2ban htop -y

### **3.2 Configuration Réseau et Pare-feu**

La VoIP traverse deux plans distincts :

* **Control Plane (SIP - UDP/TCP 5060)** : Signalisation. Cible des attaques. À restreindre aux IP de confiance (Trunk, VPN, LAN).  
* **Data Plane (RTP - UDP 10000-20000)** : Audio. Doit être ouvert largement (0.0.0.0/0) en UDP.  
* *Pourquoi ?* L'audio vient souvent de Media Gateways (SBC) de l'opérateur dont les IP sont différentes de l'IP de signalisation et peuvent changer dynamiquement.  
* **QoS (DSCP)** : Marquez les paquets sortants avec DSCP 46 (EF - Expedited Forwarding) pour qu'ils soient prioritaires sur les routeurs/switchs de l'entreprise.

## **4. LABORATOIRE : CONFIGURATION DES SERVICES (CORE)**

### **Préparation "Greenfield"**

cd /etc/asterisk  
sudo mkdir -p backups/original_conf  
sudo mv pjsip.conf extensions.conf queues.conf voicemail.conf musiconhold.conf backups/original_conf/  
sudo touch pjsip.conf pjsip_users.conf pjsip_trunk.conf extensions.conf extensions_custom.conf queues.conf voicemail.conf musiconhold.conf

### **4.1 Endpoints PJSIP : Paramètres avancés**

**pjsip.conf (Infrastructure) :**

[global]  
type=global  
user_agent=Asterisk PBX 22  
; IMPORTANT : Force le realm pour correspondre à l'attente des softphones  
default_realm=192.168.199.73

[transport-udp]  
type=transport  
protocol=udp  
bind=0.0.0.0  
local_net=192.168.1.0/24 ; Adaptez à votre réseau local

#include pjsip_users.conf  
#include pjsip_trunk.conf

**pjsip_users.conf (Utilisateurs) :**

[user-template](!)  
type=endpoint  
context=from-internal   ; Point d'entrée global pour accès aux extensions, trunks et services  
disallow=all  
; Ordre des codecs : HD (G722) > Standard Europe (ALAW/PCMA) > US (ULAW/PCMU)  
allow=g722,alaw,ulaw  
; DTMF Mode : Indispensable pour que les codes *2 et ## fonctionnent (voir section 4.4)  
dtmf_mode=rfc4733  
; direct_media=no : Asterisk reste "Man-in-the-Middle" pour l'audio.  
direct_media=no  
; force_rport=yes : Force la réponse sur le port source du paquet reçu (contournement NAT client).  
force_rport=yes  
; rewrite_contact=yes : Réécrit l'IP du header Contact (vital pour les utilisateurs nomades).  
rewrite_contact=yes  
mailboxes=${ENDPOINT}@default

[6001](user-template)  
auth=auth6001  
aors=6001  
[auth6001]  
type=auth  
auth_type=userpass  
password=1234  
username=6001  
[6001]  
type=aor  
max_contacts=2

[6002](user-template)  
auth=auth6002  
aors=6002  
[auth6002]  
type=auth  
auth_type=userpass  
password=5678  
username=6002  
[6002]  
type=aor  
max_contacts=1

### **4.2 Activation du Dialplan et des Ressources (Pré-requis Test)**

Pour permettre le premier appel de test entre 6001 et 6002, il est indispensable de configurer immédiatement le plan de numérotation, les boîtes vocales et la musique d'attente.

**extensions.conf (Le Squelette - NETTOYÉ) :**

[general]  
static=yes  
writeprotect=no

[globals]  
SDA_STANDARD=0188001122  
TRUNK=PJSIP/trunk-provider

#include extensions_custom.conf

; --- CONTEXTE PRINCIPAL ---  
; Ce contexte ne doit contenir QUE des includes.  
; NE PAS AJOUTER de lignes "exten => _X." ou de "Goto" ici,  
; sinon vous écraserez la logique des sous-contextes.  
[from-internal]  
include => local-extensions  
include => internal-services  
include => outbound-calls

**extensions_custom.conf (Logique Métier) :**

; --- Extensions Locales (Appels entre postes) ---  
[local-extensions]  
exten => _6XXX,1,NoOp(Tentative de mise en relation vers le poste ${EXTEN})  
; Ajout des options t (transfert appelé) et T (transfert appelant)  
same => n,Dial(PJSIP/${EXTEN},30,m(default)tT)  
same => n,VoiceMail(${EXTEN}@default,u)  
same => n,Hangup()

; --- Services Internes ---  
[internal-services]  
include => parkedcalls  
exten => *97,1,VoiceMailMain(${CALLERID(num)}@default)  
; File d'attente support  
exten => 800,1,Queue(support-queue,t)

; --- Appels Sortants ---  
[outbound-calls]  
; Pattern matching : 0 + 9 chiffres (Format France)  
exten => _0[1-9]XXXXXXXX,1,Set(CALLERID(all)="Societe ABC" <${SDA_STANDARD}>)  
same => n,Dial(${TRUNK}/${EXTEN})  
same => n,Hangup()

**voicemail.conf (Boîtes Vocales) :**

[general]  
format=wav49|wav  
attach=yes  
serveremail=asterisk@localhost

[default]  
; Syntaxe : extension => mot_de_passe,Nom Complet,Email  
6001 => 1234,Alice Doe,alice@example.com  
6002 => 5678,Bob Doe,bob@example.com

**musiconhold.conf (Musique d'Attente) :**

[default]  
mode=files  
directory=/var/lib/asterisk/sounds/moh  
sort=random

Rechargez les modules après création :  
dialplan reload  
module reload res_musiconhold.so  
module reload app_voicemail.so

#### **🛑 MISE EN SITUATION : TEST TRANSCODAGE**

**Objectif :** Valider la capacité de transcodage (coûteuse en CPU) maintenant que le dialplan est actif.

1. **Config :** Forcez un softphone en GSM (si dispo) et l'autre en G722.  
2. **Appel :** Lancez l'appel de 6001 vers 6002.  
3. **Observation :** core show channels affichera les formats. Le serveur décode le GSM vers PCM, puis ré-encode en G722. C'est transparent pour l'utilisateur mais charge le CPU.

### **4.3 Musique d'Attente (Théorie & Optimisation)**

Le transcodage MP3 -> SLIN -> ALAW consomme énormément de CPU. En production, **convertissez vos fichiers en WAV (8kHz, 16bit, Mono)** ou directement en .alaw pour que le serveur n'ait qu'à copier les octets vers le réseau sans traitement.

### **4.4 Gestion des Transferts, Codes Services et Diagnostic DTMF**

Sur Asterisk 22, comme sur les versions précédentes, la gestion des transferts et des services dépend largement de votre configuration. Cependant, voici les **codes standards par défaut** utilisés par la très grande majorité des systèmes.

#### **1. Transférer un appel depuis un poste**

Il existe deux types de transferts. Pour les utiliser, vous devez taper ces codes sur le clavier de votre téléphone **pendant la conversation**.

A. Transfert Assisté (Attended Transfer)  
C'est la méthode recommandée. Vous parlez au destinataire avant de lui passer l'appel.

1. Pendant l'appel, tapez ***2** (ou parfois *).  
2. L'interlocuteur est mis en attente et vous entendez "Transfert".  
3. Composez le numéro du destinataire (extension).  
4. Annoncez l'appel :  
   * **S'il accepte :** Raccrochez simplement. Les deux parties seront connectées.  
   * **S'il refuse ou ne répond pas :** Attendez que ça raccroche ou appuyez sur une touche d'annulation (souvent *) pour reprendre l'appel initial.

B. Transfert Aveugle (Blind Transfer)  
Vous transférez l'appel immédiatement sans prévenir le destinataire.

1. Pendant l'appel, tapez **##** (ou parfois #).  
2. Vous entendez "Transfert".  
3. Composez le numéro du destinataire.  
4. Raccrochez immédiatement.

**Note importante :** Si ces codes ne fonctionnent pas, c'est que la fonctionnalité "In-Call Asterisk Blind/Attended Transfer" n'est pas activée pour votre extension, ou que les codes ont été modifiés dans le fichier features.conf.

#### **2. Les Extensions (Feature Codes) Utiles**

Ces codes se composent généralement **depuis la tonalité** (comme si vous passiez un appel normal). Voici les standards les plus courants :

| Fonction | Code Standard | Description |
| :---- | :---- | :---- |
| **Renvoi inconditionnel (Activer)** | ***72** | Redirige tous les appels vers un autre numéro. |
| **Renvoi inconditionnel (Désactiver)** | ***73** | Annule le renvoi d'appel. |
| **Ne pas déranger (DND)** | ***78** | Active le mode "Ne pas déranger" (sonne occupé). |
| **Interception d'appel (Pickup)** | ***8** | Prend un appel qui sonne sur un autre poste du même groupe. |
| **Ma Messagerie** | ***97** | Consulter la boîte vocale du poste actuel. |
| **Messagerie Générale** | ***98** | Consulter la boîte vocale d'un *autre* poste. |

Parking d'Appel (Call Parking)  
Le parking permet de mettre un appel dans un "slot" public pour qu'il soit récupéré depuis n'importe quel autre poste.

1. **Parker un appel :** Faites un transfert aveugle (**##**) vers le numéro **70** (ou 700). Le système annoncera le numéro du slot (ex: *"71"*).  
2. **Récupérer un appel :** Depuis n'importe quel poste, composez le numéro du slot (ex: **71**).

**Outils de diagnostic**

* **Test d'écho (Echo Test) : *43** : Utile pour tester la latence.  
* **Horloge parlante : *60** : Pour vérifier l'heure système.

#### **3. Vérification de la configuration**

Exemple de fichier /etc/asterisk/features.conf  
Ce fichier indique à Asterisk : "Quand l'utilisateur appuie sur telle touche, déclenche telle action".  
[general]  
transferdigittimeout => 3  
parkext => 700           ; Parfois géré dans res_parking.conf  
context => parkedcalls   ; Le contexte où atterrissent les appels garés

[featuremap]  
blindxfer => ##          ; Transfert Aveugle  
atxfer => *2             ; Transfert Assisté  
disconnect => *0         ; Raccrocher  
automon => *1            ; Enregistrement à la volée  
parkcall => #72          ; Parking direct

**Points Importants pour que ça fonctionne**

1. **Les options de la commande Dial()** : Dans extensions.conf, vous **devez** ajouter les options t ou T.  
   * t : L'appelé peut transférer.  
   * T : L'appelant peut transférer.  
   * *Exemple :* Dial(PJSIP/${EXTEN},30,tT)  
2. **Le module Parking** : Assurez-vous que res_parking.so est chargé et configuré dans res_parking.conf.

#### **4. Diagnostic DTMF (Si les touches ne marchent pas)**

C'est un problème classique. Si Asterisk et votre téléphone ne parlent pas la même "langue" pour les touches, Asterisk n'entendra jamais le ##.

**Diagnostiquer le DTMF en temps réel**

1. Dans la console Asterisk (asterisk -rvvv), activez le debug RTP : rtp set debug on  
2. Passez un appel et appuyez sur une touche (ex: **5**).  
* **Scénario A (Succès) :** Vous voyez Got RTP RFC2833 ... Event: 5. Asterisk reçoit le code.  
* **Scénario B (Échec) :** Vous ne voyez que des paquets audio. Votre téléphone envoie en "Inband" ou "SIP INFO".

Corriger la configuration (PJSIP)  
Dans pjsip_users.conf, forcez le mode standard :  
[user-template](!)  
; ...  
dtmf_mode=rfc4733  
; ...

*Note : Sur le softphone (ex: MicroSIP), réglez aussi le "DTMF Mode" sur **RFC 2833** ou **Auto** (Jamais Inband).*

### **4.5 Call Center : Stratégies ACD**

**queues.conf :**

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

#### **🛑 MISE EN SITUATION : TEST QUEUE & ANALYTICS**

1. **Action :** Bob (6002) refuse l'appel.  
2. **Appel :** Appelez le 800.  
3. **Observation :** queue show support-queue. L'appelant est en attente.  
4. **Logs :** Vérifiez /var/log/asterisk/queue_log. Chaque événement (ENTERQUEUE, CONNECT, ABANDON) est tracé pour les statistiques (SLA, Temps moyen d'attente).

### **4.6 Interconnexion Trunk SIP**

La gestion des **Timers** et du **Keepalive** est vitale pour détecter une coupure de lien opérateur.

**pjsip_trunk.conf :**

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
context=outbound-calls   ; Notez le changement de contexte si nécessaire selon votre dialplan  
disallow=all  
allow=ulaw,alaw          ; G.711 standard opérateur.  
outbound_auth=auth-trunk  
aors=trunk-provider  
from_user=LOGIN          ; Force le header 'From' (Anti-spoofing opérateur).  
qualify_frequency=60     ; Envoie un SIP OPTIONS toutes les 60s. Si pas de réponse, marque le trunk "Unavail".

[trunk-provider]  
type=aor  
contact=sip:sip.provider.com

## **5. LABORATOIRE : ENGINEERING AVANCÉ DU DIALPLAN**

Les fichiers de base (extensions.conf, extensions_custom.conf) ont été créés dans la section 4.2 pour permettre les tests immédiats. Cette section se concentre sur les logiques avancées que nous avons intégrées.

### **5.1 Pattern Matching et Variables**

Dans extensions_custom.conf, nous avons utilisé _6XXX pour capturer tous les numéros de 4 chiffres commençant par 6.

* ${EXTEN} : Variable contenant le numéro composé.  
* ${CALLERID(num)} : Variable contenant le numéro de l'appelant.

### **5.2 Expérience Appelant (Early Media)**

Dans le contexte [outbound-calls], l'utilisation de Dial() génère souvent une sonnerie factice (Ringing). Pour des services interactifs, il est parfois nécessaire d'utiliser Progress() pour signaler un 183 Session Progress (Early Media) avant de décrocher.

### **5.3 IVR Dynamique**

L'IVR (*Interactive Voice Response*) permet d'aiguiller l'appel. Vous pouvez ajouter ce contexte à votre extensions_custom.conf :

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

#### **🛑 MISE EN SITUATION FINALE : VALIDATION GLOBALE**

1. **Action :** Appelez votre numéro public depuis un mobile.  
2. **Vérification :**  
* Entendez-vous le message d'accueil ? (Preuve que le flux RTP entrant passe le NAT).  
* Entendez-vous la musique d'attente "Commercial" ?  
* La qualité est-elle bonne ? (Pas de gigue/hachures).

## **6. INTERCONNEXION SITE-À-SITE (IAX2)**

### **6.1 Avantages protocolaires**

IAX2 (Inter-Asterisk eXchange) est supérieur au SIP pour les liens inter-sites :

* **NAT Friendly** : Un seul port **UDP 4569** pour la signalisation ET l'audio. Pas de plage RTP dynamique à ouvrir.  
* **Trunking (Multiplexage)** : Si 10 appels simultanés passent, IAX2 ne génère qu'un seul en-tête IP contenant 10 payloads audio. Économie massive de bande passante (overhead réduit).

### **6.2 Configuration du Tunnel**

**iax.conf :**

[site-distant]  
type=friend  
host=1.2.3.4       ; IP du site distant  
username=paris  
secret=SuperSecretTunnel  
context=local-extensions ; Les appels arrivent directement dans le plan de numérotation interne.  
trunk=yes          ; Active le mode multiplexage.  
requirecalltoken=no  
encryption=yes     ; Active le chiffrement natif (sécurité type VPN).

## **7. MAINTENANCE ET ANALYSE**

### **7.1 Analyse SIP temps réel (sngrep)**

sngrep est votre tableau de bord réseau.

* **401 Unauthorized** : Normal lors de l'enregistrement (Challenge/Response).  
* **403 Forbidden** : Erreur critique (Mot de passe faux, IP bannie par Fail2Ban, ou CallerID sortant non autorisé par l'opérateur).  
* **408 Request Timeout** : Le paquet part mais ne revient pas (Pare-feu bloquant ou IP destination injoignable).

### **7.2 Analyse RTP Forensic (Wireshark)**

Le SIP fonctionne (le téléphone sonne), mais l'audio est hachuré, robotique ou absent (One Way Audio) ? C'est un problème de transport RTP.

1. **Capture Serveur (Full Payload) :**

# Capture brute sur l'interface (-i any) sans tronquer les paquets (-s 0)  
sudo tcpdump -i any -s 0 -w /tmp/debug_audio.pcap udp port 5060 or udp portrange 10000-20000

2. **Analyse Wireshark (Poste Admin) :**  
* Récupérez le fichier .pcap.  
* Menu **Téléphonie -> Appels VoIP -> Analyser -> Lire les flux**.  
* **Écoute** : Vous pouvez écouter l'audio tel qu'il a été vu par la carte réseau du serveur.  
* Si le son est clair ici mais mauvais au téléphone : Problème réseau local (WiFi, Switch).  
* Si le son est mauvais ici (trous, glitchs) : Problème en amont (Lien opérateur, perte de paquets WAN).
