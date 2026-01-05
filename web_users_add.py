# Asterisk_Web_Admin

Plutôt que d'installer une "usine à gaz" qui écraserait tout votre travail manuel, je vous propose de créer **votre propre mini-interface web d'administration** en Python (avec le framework léger Flask).

Ce script va :

1. Afficher un formulaire Web.
2. Écrire les configurations directement dans vos fichiers `.conf`.
3. Recharger Asterisk automatiquement.

Voici le code complet de votre application d'administration.

### Comment installer et lancer votre interface

Cette interface est très légère et utilise Python, qui est déjà installé sur votre Debian.

#### 1. Installer Flask (le mini-serveur web)

```bash
apt install python3-flask -y
# Ou si pip est préféré : pip3 install flask

#### 2. Créer le fichier
Copiez le code ci-dessus dans un fichier nommé `/root/asterisk_admin.py` sur votre serveur.

#### 3. Lancer l'application
Puisque le script doit modifier des fichiers dans `/etc/asterisk`, il doit être lancé en **root**.

```bash
python3 /root/asterisk_admin.py

#### 4. Utilisation
Ouvrez votre navigateur et allez sur : `http://IP_DE_VOTRE_SERVEUR:5000`

Remplissez le formulaire (ex: Extension **7003**, Nom **Charlie**, Pass **Secret**).
Dès que vous validez :
1.  Le script ajoute les lignes dans `pjsip_users.conf` et `voicemail.conf`.
2.  Il exécute les commandes de reload Asterisk.
3.  La ligne est immédiatement fonctionnelle (si vous restez dans la plage 6XXX ou 7XXX couverte par votre dialplan actuel).

```


import os
import subprocess
import re
from flask import Flask, request, render_template_string

# --- CONFIGURATION ---
# Chemins vers vos fichiers Asterisk (Adaptez si besoin)
CONF_DIR = "/etc/asterisk"
PJSIP_FILE = os.path.join(CONF_DIR, "pjsip_users.conf")
VOICEMAIL_FILE = os.path.join(CONF_DIR, "voicemail.conf")
EXT_CUSTOM_FILE = os.path.join(CONF_DIR, "extensions_custom.conf")

app = Flask(__name__)

# --- TEMPLATE HTML (Interface Web) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Asterisk Lab Admin</title>
    <style>
        body { font-family: sans-serif; max-width: 600px; margin: 40px auto; background: #f4f4f4; }
        .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #d35400; text-align: center; }
        label { display: block; margin-top: 15px; font-weight: bold; }
        input { width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box;}
        button { margin-top: 20px; width: 100%; background: #2c3e50; color: white; border: none; padding: 10px; cursor: pointer; font-size: 16px; border-radius: 4px;}
        button:hover { background: #34495e; }
        .success { color: green; text-align: center; margin-top: 20px; }
        .error { color: red; text-align: center; margin-top: 20px; }
        .info { color: #2980b9; text-align: center; margin-top: 10px; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📞 Création de Ligne SIP</h1>
        <form method="POST">
            <label>Numéro d'Extension (ex: 7003)</label>
            <input type="number" name="extension" required placeholder="7003">
            
            <label>Nom Complet (ex: John Doe)</label>
            <input type="text" name="name" required placeholder="John Doe">
            
            <label>Mot de Passe SIP</label>
            <input type="text" name="password" required placeholder="SecretPass123">
            
            <label>Email (pour Voicemail)</label>
            <input type="email" name="email" required placeholder="john@example.com">
            
            <button type="submit">Créer et Recharger Asterisk</button>
        </form>
        
        {% if message %}
            <div class="{{ status }}">{{ message }}</div>
        {% endif %}
        {% if detail %}
            <div class="info">{{ detail }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

# --- FONCTIONS BACKEND ---

def reload_asterisk():
    """Recharge la configuration Asterisk via la commande console"""
    try:
        # On recharge PJSIP, le Dialplan et le Voicemail
        subprocess.run(['asterisk', '-rx', 'pjsip reload'], check=True)
        subprocess.run(['asterisk', '-rx', 'dialplan reload'], check=True)
        subprocess.run(['asterisk', '-rx', 'module reload app_voicemail.so'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def add_pjsip_user(ext, password):
    """Ajoute le bloc utilisateur dans pjsip_users.conf"""
    # On utilise le template [user-template] défini dans votre Lab
    config_block = f"""
; --- Ajout Web {ext} ---
[{ext}](user-template)
auth=auth{ext}
aors={ext}
[auth{ext}]
type=auth
auth_type=userpass
password={password}
username={ext}
[{ext}]
type=aor
max_contacts=1
"""
    with open(PJSIP_FILE, "a") as f:
        f.write(config_block)

def add_voicemail_user(ext, password, name, email):
    """Ajoute la ligne dans voicemail.conf"""
    # Syntaxe: extension => password,Name,Email
    line = f"{ext} => {password},{name},{email}\n"
    
    # On cherche le contexte [default] pour insérer après (simplification: ajout à la fin)
    with open(VOICEMAIL_FILE, "a") as f:
        f.write(line)

def check_and_update_dialplan(ext):
    """
    Vérifie si le routage pour la plage (ex: _8XXX) existe.
    Sinon, ajoute un bloc dédié pour cette plage à la fin du fichier extensions_custom.conf.
    Asterisk fusionnera automatiquement ce bloc avec le contexte [local-extensions] existant.
    """
    first_digit = str(ext)[0]
    target_pattern = f"_{first_digit}XXX"
    
    try:
        with open(EXT_CUSTOM_FILE, "r") as f:
            content = f.read()

        # On cherche si "exten => _8XXX" (ou _[...]) existe déjà dans le fichier
        # On fait une recherche simple pour voir si le pattern est déjà défini
        if f"exten => {target_pattern}" in content:
            return False, None # Déjà présent
            
        # Si absent, on ajoute le bloc complet à la fin du fichier
        # Note : Ré-ouvrir le contexte [local-extensions] est valide, Asterisk fusionne les blocs.
        new_block = f"""
; --- Ajout Automatique Plage {first_digit}XXX ---
[local-extensions]
exten => {target_pattern},1,NoOp(Appel vers le poste ${{EXTEN}})
same => n,Dial(PJSIP/${{EXTEN}},30,m(default)tT)
same => n,VoiceMail(${{EXTEN}}@default,u)
same => n,Hangup()
"""
        with open(EXT_CUSTOM_FILE, "a") as f:
            f.write(new_block)
            
        return True, f"Nouveau bloc de routage créé pour la plage {target_pattern}"

    except Exception as e:
        return False, f"Erreur modification dialplan: {str(e)}"

# --- ROUTE FLASK ---

@app.route('/', methods=['GET', 'POST'])
def home():
    message = ""
    status = ""
    detail = ""
    
    if request.method == 'POST':
        ext = request.form.get('extension')
        name = request.form.get('name')
        pwd = request.form.get('password')
        email = request.form.get('email')
        
        try:
            # 1. Écriture dans les fichiers PJSIP et Voicemail
            add_pjsip_user(ext, pwd)
            add_voicemail_user(ext, "1234", name, email) # PIN voicemail par défaut 1234
            
            # 2. Ajout d'un bloc Dialplan si nécessaire (ex: _8XXX)
            updated, dp_msg = check_and_update_dialplan(ext)
            if updated:
                detail = dp_msg
            
            # 3. Rechargement Asterisk
            if reload_asterisk():
                message = f"Succès ! L'extension {ext} ({name}) a été créée et Asterisk rechargé."
                status = "success"
            else:
                message = "Fichiers écrits, mais erreur lors du reload Asterisk."
                status = "error"
                
        except Exception as e:
            message = f"Erreur système : {str(e)}"
            status = "error"

    return render_template_string(HTML_TEMPLATE, message=message, status=status, detail=detail)

if __name__ == '__main__':
    # Écoute sur toutes les interfaces (0.0.0.0) port 5000
    # ATTENTION : À lancer en root pour avoir le droit d'écrire dans /etc/asterisk
    app.run(host='0.0.0.0', port=5000, debug=True)
