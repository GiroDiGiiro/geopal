"""Texte d'aide affiché dans le QTextBrowser du formulaire Post Canoë vers GEP."""

HELP_TEXT_POST_CANOE_TO_GEP = """
<h2 style="color:#2E7D32;">Aide — Post-traitement Canoë vers GEP</h2>

<p>
Cet outil permet de reporter les informations d'une couche réseau issue de
<b style="color:#1565C0;">Canoë</b> sur une couche
<b style="color:#1565C0;">GEP</b>, afin de produire une couche fusionnée
prête à être intégrée.
</p>

<div style="background:#E8F5E9;border-left:5px solid #4CAF50;padding:8px;margin:10px 0;">
<b>Deux méthodes de correspondance sont disponibles :</b>
<ul>
<li>Correspondance par identifiant (recommandée).</li>
<li>Correspondance par localisation géographique.</li>
</ul>
</div>

<h3 style="color:#1565C0;">1. Couches à sélectionner</h3>

<ul>
<li><b>Couche Canoë</b> : couche réseau exportée depuis Canoë contenant les
résultats de modélisation (débits, cotes, pente, etc.).</li>

<li><b>Couche GEP</b> : couche de référence du réseau contenant les
informations de gestion (bassin versant, gestionnaire, commune...).</li>

<li><b>Couche de sortie</b> : couche recevant les nouvelles entités fusionnées
(attributs Canoë + GEP).</li>
</ul>

<div style="background:#FFF3E0;border-left:5px solid #FB8C00;padding:8px;margin:10px 0;">
<b>Important</b><br/>
Les trois couches doivent être différentes. Si deux couches identiques sont
sélectionnées, le bouton <b>OK</b> est désactivé.
</div>

<h3 style="color:#1565C0;">2. Méthodes de correspondance</h3>

<h4 style="color:#2E7D32;">A. Correspondance par identifiant <small>(recommandée)</small></h4>

<p>
Chaque tronçon Canoë est associé à un tronçon GEP en comparant un champ
identifiant commun.
</p>

<p><b>Paramètres :</b></p>

<ul>
<li><b>Champ identifiant (Canoë)</b></li>
<li><b>Champ identifiant (GEP)</b></li>
<li><b>Géométrie à conserver</b>
    <ul>
        <li>Géométrie Canoë</li>
        <li>Géométrie GEP</li>
    </ul>
</li>
</ul>

<div style="background:#E3F2FD;border-left:5px solid #2196F3;padding:8px;margin:10px 0;">
<b>✔ Conseil</b><br/>
Cette méthode est la plus fiable lorsque les deux couches possèdent un
identifiant commun cohérent.
</div>

<h4 style="color:#2E7D32;">B. Correspondance par localisation</h4>

<p>
Chaque tronçon Canoë est comparé géométriquement aux tronçons GEP.
Le premier tronçon dont la géométrie <b>intersecte</b> celle de Canoë est
retenu.
</p>

<p><b>À retenir :</b></p>

<ul>
<li>Aucun identifiant commun n'est nécessaire.</li>
<li>La correspondance repose uniquement sur la géométrie.</li>
<li>Certaines entités peuvent ne trouver aucune correspondance.</li>
<li>Une vérification visuelle après traitement est conseillée.</li>
</ul>

<div style="background:#FFF8E1;border-left:5px solid #F9A825;padding:8px;margin:10px 0;">
<b>⚠️ Attention</b><br/>
Cette méthode est moins fiable que la correspondance par identifiant,
notamment lorsque les réseaux sont légèrement décalés.
</div>

<h3 style="color:#1565C0;">3. Entités sans correspondance</h3>

<p>
Les tronçons Canoë sans correspondance sont automatiquement copiés dans une
couche mémoire nommée :
</p>

<p style="margin-left:20px;">
<i style="color:#C62828;">
Error : Correspondance non trouvée entre couche réseau et post Canoë
</i>
</p>

<p>
Cette couche permet de localiser rapidement les tronçons nécessitant une
vérification ou une correction.
</p>

<h3 style="color:#1565C0;">4. Fin du traitement</h3>

<p>
À la fin de l'exécution, un message récapitulatif indique le nombre de
correspondances trouvées.
</p>

<div style="background:#ECEFF1;border-left:5px solid #607D8B;padding:8px;margin:10px 0;">
<b>Exemple :</b><br/>
<i>Terminé : 152/160 correspondances trouvées sur les entités de Canoë analysées.</i>
</div>
"""