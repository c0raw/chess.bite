# chess.bot

<h1 align="center">♟️ Chess.bot</h1>
<h3 align="center">Jeu d’échecs en Python — Projet NSI Terminale 2025</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/Interface-Tkinter-green.svg" alt="Tkinter">
</p>

<h2 align="center">🚀 Présentation</h2>

<p><strong>Chess.bot</strong> est un jeu d’échecs complet développé dans le cadre d'un <strong>projet de NSI en terminale</strong> 🧩.<br>
Il offre une expérience interactive entre deux joueurs humains <strong>ou contre une IA multi-niveaux</strong>.</p>

<h3>🎯 Caractéristiques principales</h3>

<ul>
  <li>🧠 <strong>IA évolutive</strong> : du niveau <em>Facile</em> au mode <em>Impossible</em> (Minimax + Alpha-Bêta)</li>
  <li>🎨 <strong>Interface graphique</strong> intuitive (Tkinter)</li>
  <li>💾 <strong>Sauvegarde & chargement</strong> de parties (format JSON)</li>
  <li>⏱️ <strong>Chronomètre</strong> intégré pour chaque joueur</li>
  <li>↩️ <strong>Annulation du dernier coup</strong> (pile + liste chaînée)</li>
  <li>♜ <strong>Règles officielles</strong> d’échecs : roque, prise en passant, promotion, échec, mat, pat…</li>
</ul>

<hr>

<h2>🧩 Structure du projet</h2>

<pre>
chess.bot/
│
├── engine/
│   ├── ai.py              → Fonctions d’intelligence artificielle (5 niveaux)
│   ├── board.py           → Représentation du plateau et des coordonnées
│   ├── movegen.py         → Génération des coups légaux et détection d’échec/mat
│   ├── timecontrol.py     → Gestion du chronomètre et état de la partie
│   ├── pile_liste.py      → Pile (Pile_LIFO) & Liste chaînée (Liste_chaine)
│
├── ui_game.py             → Interface graphique Tkinter + logique de jeu principale
├── main.py                → Point d’entrée du programme
└── README.md
</pre>

<hr>

<h2>🧠 Intelligence Artificielle</h2>

<p>L’IA repose sur différents <strong>niveaux de difficulté</strong> définis dans <code>engine/ai.py</code> :</p>

<table>
  <thead>
    <tr>
      <th>Niveau</th>
      <th>Fonction</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>🎲 <strong>Facile</strong></td><td><code>ai_easy()</code></td><td>Joue aléatoirement parmi les coups légaux</td></tr>
    <tr><td>🧩 <strong>Naïf</strong></td><td><code>ai_naive()</code></td><td>Privilégie les captures simples</td></tr>
    <tr><td>⚖️ <strong>Moyen</strong></td><td><code>ai_normal()</code></td><td>Anticipe un coup avec évaluation du matériel</td></tr>
    <tr><td>🧮 <strong>Difficile</strong></td><td><code>ai_complex()</code></td><td>Utilise Minimax (profondeur 2)</td></tr>
    <tr><td>🧠 <strong>Expert</strong></td><td><code>ai_impossible()</code></td><td>Minimax + élagage Alpha-Bêta</td></tr>
  </tbody>
</table>

<hr>

<h2>⚙️ Structures de données</h2>

<h3>🧱 Pile (<code>Pile_LIFO</code>)</h3>

<p>Implémentée dans <code>engine/pile_liste.py</code>.</p>

<ul>
  <li><strong>Type :</strong> LIFO (Last In, First Out)</li>
  <li><strong>Utilisation :</strong> gérer l’historique des coups (fonction “Annuler le dernier coup”)</li>
</ul>

<pre><code class="language-python">
Pile_LIFO.push(coup)
Pile_LIFO.pop()
</code></pre>

<h3>🔗 Liste chaînée (<code>Liste_chaine</code>)</h3>

<p>Également dans <code>engine/pile_liste.py</code>.</p>

<ul>
  <li><strong>Utilisation :</strong> mémoriser la succession des états du plateau</li>
  <li><strong>Fonctions :</strong>
    <ul>
      <li><code>append()</code> → ajoute un état du jeu</li>
      <li><code>pop_last()</code> → supprime le dernier état (pour revenir en arrière)</li>
    </ul>
  </li>
</ul>

<p>Ces deux structures sont intégrées au cœur du gameplay.</p>

<hr>

<h2>💻 Interface graphique (Tkinter)</h2>

<ul>
  <li>Affichage du plateau 8×8 et des pièces ♔♕♖♗♘♙</li>
  <li>Sélection des cases à la souris</li>
  <li>Gestion du temps et des coups</li>
  <li>Fenêtres pour : nouvelle partie, sauvegarde/chargement, promotion, annulation, etc.</li>
</ul>

<hr>

<h2>🕹️ Fonctionnalités principales</h2>

<ul>
  <li>✅ Jeu à 2 joueurs ou contre IA</li>
  <li>✅ 5 niveaux de difficulté</li>
  <li>✅ Règles d’échecs complètes</li>
  <li>✅ Sauvegarde / chargement (JSON)</li>
  <li>✅ Chronomètre individuel</li>
  <li>✅ Annulation du dernier coup</li>
  <li>✅ Interface user friendly</li>
  <li>✅ Code structuré</li>
</ul>

<hr>

<h2>▶️ Installation & Exécution</h2>

<ol>
  <li><strong>Cloner le dépôt :</strong></li>
</ol>

<pre><code class="language-bash">
git clone https://github.com/&lt;ton-utilisateur&gt;/chess.bot.git
cd chess.bot
</code></pre>

<ol start="2">
  <li><strong>Lancer le jeu :</strong></li>
</ol>

<pre><code class="language-bash">
python main.py
</code></pre>

<hr>

<h2>👨‍💻 Auteurs</h2>

<table>
  <tr><th>Rôle</th><th>Nom</th></tr>
  <tr><td>🧑‍💻 Développeurs</td><td>Waroc, Tom, Marwan, Léo</td></tr>
  <tr><td>📆 Année</td><td>2025–2026</td></tr>
  <tr><td>💬 Langage</td><td>Python 3</td></tr>
   <tr><td>⚖️ Licence</td><td>MIT</td></tr>
</table>

<hr>

<p align="center"><em>♟️ Chess.bot — Le plaisir du code et des échecs.</em></p>
