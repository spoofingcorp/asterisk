# Installation de XiVO sur Debian 12 (Bookworm)

Ce guide détaille les étapes pour installer XiVO sur une machine virtuelle Debian 12 sans interface graphique.

Source: https://myitknowledge.fr/installation-xivo-debian-12/

## Prérequis

* **OS :** Debian 12 (Bookworm) - Installation minimale (Netinst / No GUI).
* **Accès :** Privilèges root.

---

## 1. Configuration de l'accès SSH (Root)

Par défaut, Debian désactive la connexion SSH directe en root.

1. Éditez le fichier de configuration SSH :
```bash
nano /etc/ssh/sshd_config

```


2. Modifiez ou ajoutez la ligne suivante :
```ssh
PermitRootLogin yes

```


3. Redémarrez le service SSH pour appliquer les changements :
```bash
systemctl restart ssh

```



> **Note de sécurité :** Sur un environnement de production exposé, il est recommandé d'utiliser une authentification par clé SSH plutôt que par mot de passe pour le compte root.

---

## 2. Configuration des dépôts APT

Connectez-vous à la VM via SSH pour la suite des opérations. Il est nécessaire de nettoyer les sources pour éviter l'utilisation du CD-ROM.

1. Éditez le fichier `sources.list` :
```bash
nano /etc/apt/sources.list

```


2. Commentez la ligne commençant par `deb cdrom:...` et assurez-vous que le fichier ressemble à ceci :
```sources.list
# deb cdrom:[Debian GNU/Linux 12.8.0 _Bookworm_ - Official amd64 DVD Binary-1 with firmware 20241109-11:05]/ bookworm contrib main non-free-firmware

deb http://deb.debian.org/debian/ bookworm main non-free-firmware
deb-src http://deb.debian.org/debian/ bookworm main non-free-firmware

deb http://security.debian.org/debian-security bookworm-security main non-free-firmware
deb-src http://security.debian.org/debian-security bookworm-security main non-free-firmware

# bookworm-updates
deb http://deb.debian.org/debian/ bookworm-updates main non-free-firmware
deb-src http://deb.debian.org/debian/ bookworm-updates main non-free-firmware

```


3. Mettez à jour la liste des paquets :
```bash
apt-get update

```



---

## 3. Installation de XiVO

### Installation des dépendances

Installez les outils nécessaires pour récupérer le script d'installation :

```bash
apt-get install -y curl wget

```

### Lancement du script d'installation

Exécutez les commandes suivantes pour télécharger et lancer l'installateur XiVO :

```bash
# Télécharger le script
wget http://mirror.xivo.solutions/xivo_install.sh

# Rendre le script exécutable
chmod +x xivo_install.sh

# Lancer l'installation
./xivo_install.sh

```

> **⚠️ Important :** L'installation de Docker et des conteneurs XiVO peut prendre entre **20 et 60 minutes** selon votre connexion internet et la puissance CPU.
> **Ne surtout pas interrompre le processus** (pas de `Ctrl+C` ou `Ctrl+X`).

---

## 4. Accès à l'interface d'administration

Une fois l'installation terminée :

1. Récupérez l'adresse IP de votre machine virtuelle :
```bash
ip a

```


2. Ouvrez votre navigateur web et accédez à l'interface via :
`http://<IP_DE_LA_VM>`

---

## 5. Commandes utiles (Debug Asterisk)

Voici quelques commandes pour vérifier le bon fonctionnement du moteur Asterisk ou pour déboguer le protocole PJSIP via la CLI.

Entrer dans la console Asterisk :

```bash
asterisk -rvvvvv

```

Commandes de diagnostic PJSIP (à taper dans la console Asterisk) :

```bash
# Voir les enregistrements (Trunks / Postes)
pjsip show registrations

# Voir les points de terminaison (Endpoints)
pjsip show endpoints

# Voir les canaux actifs (Appels en cours)
pjsip show channels

```

---
