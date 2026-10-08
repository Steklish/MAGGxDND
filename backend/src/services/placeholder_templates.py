"""
backend/src/services/placeholder_templates.py

Pre-bundled, valid vector SVG placeholders for MAGGxDND visual assets.
Includes 18 thematic SVG designs across characters, items, scenes, and battlemaps.
"""

BUNDLED_PLACEHOLDERS = {
    "character_default.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <radialGradient id="bg-grad" cx="50%" cy="40%" r="60%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#090d16"/>
    </radialGradient>
    <linearGradient id="gold-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fbbf24"/>
      <stop offset="100%" stop-color="#b45309"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <rect width="512" height="512" rx="32" fill="url(#bg-grad)"/>
  <rect x="16" y="16" width="480" height="480" rx="24" fill="none" stroke="url(#gold-grad)" stroke-width="2" opacity="0.6"/>
  <!-- Adventurer Silhouette -->
  <circle cx="256" cy="180" r="64" fill="none" stroke="url(#gold-grad)" stroke-width="4" filter="url(#glow)"/>
  <circle cx="256" cy="180" r="52" fill="#334155"/>
  <path d="M 160 360 C 160 280, 210 260, 256 260 C 302 260, 352 280, 352 360 C 352 390, 330 400, 256 400 C 182 400, 160 390, 160 360 Z" fill="#334155" stroke="url(#gold-grad)" stroke-width="3"/>
  <!-- Star Sigil -->
  <polygon points="256,140 266,170 298,170 272,190 282,220 256,200 230,220 240,190 214,170 246,170" fill="url(#gold-grad)" opacity="0.8"/>
  <text x="256" y="440" fill="#f8fafc" font-family="system-ui, sans-serif" font-size="20" font-weight="bold" letter-spacing="4" text-anchor="middle">ADVENTURER</text>
  <text x="256" y="465" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="12" letter-spacing="2" text-anchor="middle">MAGGxDND HERO PROFILE</text>
</svg>""",

    "character_warrior.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <radialGradient id="bg-warrior" cx="50%" cy="45%" r="65%">
      <stop offset="0%" stop-color="#2d1215"/>
      <stop offset="100%" stop-color="#0a0506"/>
    </radialGradient>
    <linearGradient id="steel-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f87171"/>
      <stop offset="50%" stop-color="#dc2626"/>
      <stop offset="100%" stop-color="#7f1d1d"/>
    </linearGradient>
    <linearGradient id="blade" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#cbd5e1"/>
      <stop offset="50%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#64748b"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="32" fill="url(#bg-warrior)"/>
  <rect x="16" y="16" width="480" height="480" rx="24" fill="none" stroke="url(#steel-grad)" stroke-width="2" opacity="0.7"/>
  <!-- Shield Outline -->
  <path d="M 256 100 Q 350 100 350 200 C 350 310 256 370 256 370 C 256 370 162 310 162 200 Q 162 100 256 100 Z" fill="#1e1b1e" stroke="url(#steel-grad)" stroke-width="6"/>
  <!-- Crossed Swords -->
  <line x1="180" y1="130" x2="332" y2="330" stroke="url(#blade)" stroke-width="8" stroke-linecap="round"/>
  <line x1="332" y1="130" x2="180" y2="330" stroke="url(#blade)" stroke-width="8" stroke-linecap="round"/>
  <line x1="160" y1="150" x2="200" y2="110" stroke="#fca5a5" stroke-width="12" stroke-linecap="round"/>
  <line x1="352" y1="150" x2="312" y2="110" stroke="#fca5a5" stroke-width="12" stroke-linecap="round"/>
  <circle cx="256" cy="225" r="28" fill="#991b1b" stroke="#fecaca" stroke-width="3"/>
  <text x="256" y="440" fill="#fecaca" font-family="system-ui, sans-serif" font-size="22" font-weight="bold" letter-spacing="4" text-anchor="middle">WARRIOR</text>
  <text x="256" y="465" fill="#f87171" font-family="system-ui, sans-serif" font-size="12" letter-spacing="2" text-anchor="middle">MARTIAL COMBATANT</text>
</svg>""",

    "character_wizard.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <radialGradient id="bg-wizard" cx="50%" cy="40%" r="65%">
      <stop offset="0%" stop-color="#1e1035"/>
      <stop offset="100%" stop-color="#090514"/>
    </radialGradient>
    <linearGradient id="arcane-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#c084fc"/>
      <stop offset="50%" stop-color="#a855f7"/>
      <stop offset="100%" stop-color="#4c1d95"/>
    </linearGradient>
    <linearGradient id="cyan-glow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="32" fill="url(#bg-wizard)"/>
  <rect x="16" y="16" width="480" height="480" rx="24" fill="none" stroke="url(#arcane-grad)" stroke-width="2" opacity="0.7"/>
  <!-- Arcane Rune Ring -->
  <circle cx="256" cy="220" r="110" fill="none" stroke="url(#arcane-grad)" stroke-width="2" stroke-dasharray="12, 6"/>
  <circle cx="256" cy="220" r="85" fill="none" stroke="url(#cyan-glow)" stroke-width="3"/>
  <polygon points="256,145 320,256 192,256" fill="none" stroke="url(#arcane-grad)" stroke-width="3"/>
  <polygon points="256,295 192,184 320,184" fill="none" stroke="url(#cyan-glow)" stroke-width="3"/>
  <!-- Mystic Orb -->
  <circle cx="256" cy="220" r="30" fill="url(#cyan-glow)" opacity="0.8"/>
  <text x="256" y="440" fill="#e9d5ff" font-family="system-ui, sans-serif" font-size="22" font-weight="bold" letter-spacing="4" text-anchor="middle">WIZARD</text>
  <text x="256" y="465" fill="#a855f7" font-family="system-ui, sans-serif" font-size="12" letter-spacing="2" text-anchor="middle">ARCANE SCHOLAR</text>
</svg>""",

    "character_rogue.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <radialGradient id="bg-rogue" cx="50%" cy="45%" r="65%">
      <stop offset="0%" stop-color="#062b1b"/>
      <stop offset="100%" stop-color="#030f0a"/>
    </radialGradient>
    <linearGradient id="emerald-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#34d399"/>
      <stop offset="50%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#064e3b"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="32" fill="url(#bg-rogue)"/>
  <rect x="16" y="16" width="480" height="480" rx="24" fill="none" stroke="url(#emerald-grad)" stroke-width="2" opacity="0.7"/>
  <!-- Hood and Daggers -->
  <path d="M 256 120 C 180 120, 160 200, 160 270 C 180 270, 210 250, 256 250 C 302 250, 332 270, 352 270 C 352 200, 332 120, 256 120 Z" fill="#0f172a" stroke="url(#emerald-grad)" stroke-width="3"/>
  <!-- Shadow Mask Eyes -->
  <ellipse cx="220" cy="205" rx="14" ry="6" fill="#34d399"/>
  <ellipse cx="292" cy="205" rx="14" ry="6" fill="#34d399"/>
  <!-- Dual Daggers -->
  <path d="M 190 280 L 150 370 L 170 370 L 210 280 Z" fill="#94a3b8" stroke="#34d399" stroke-width="2"/>
  <path d="M 322 280 L 362 370 L 342 370 L 302 280 Z" fill="#94a3b8" stroke="#34d399" stroke-width="2"/>
  <text x="256" y="440" fill="#a7f3d0" font-family="system-ui, sans-serif" font-size="22" font-weight="bold" letter-spacing="4" text-anchor="middle">ROGUE</text>
  <text x="256" y="465" fill="#34d399" font-family="system-ui, sans-serif" font-size="12" letter-spacing="2" text-anchor="middle">SHADOW INFILTRATOR</text>
</svg>""",

    "character_cleric.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <radialGradient id="bg-cleric" cx="50%" cy="40%" r="65%">
      <stop offset="0%" stop-color="#3b2b07"/>
      <stop offset="100%" stop-color="#120e03"/>
    </radialGradient>
    <linearGradient id="divine-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fef08a"/>
      <stop offset="50%" stop-color="#eab308"/>
      <stop offset="100%" stop-color="#854d0e"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="32" fill="url(#bg-cleric)"/>
  <rect x="16" y="16" width="480" height="480" rx="24" fill="none" stroke="url(#divine-grad)" stroke-width="2" opacity="0.7"/>
  <!-- Sunburst Holy Emblem -->
  <circle cx="256" cy="220" r="60" fill="none" stroke="url(#divine-grad)" stroke-width="6"/>
  <!-- Sun Rays -->
  <line x1="256" y1="120" x2="256" y2="145" stroke="url(#divine-grad)" stroke-width="6" stroke-linecap="round"/>
  <line x1="256" y1="295" x2="256" y2="320" stroke="url(#divine-grad)" stroke-width="6" stroke-linecap="round"/>
  <line x1="156" y1="220" x2="181" y2="220" stroke="url(#divine-grad)" stroke-width="6" stroke-linecap="round"/>
  <line x1="331" y1="220" x2="356" y2="220" stroke="url(#divine-grad)" stroke-width="6" stroke-linecap="round"/>
  <!-- Holy Cross/Mace -->
  <line x1="256" y1="170" x2="256" y2="270" stroke="#fef08a" stroke-width="8" stroke-linecap="round"/>
  <line x1="220" y1="200" x2="292" y2="200" stroke="#fef08a" stroke-width="8" stroke-linecap="round"/>
  <text x="256" y="440" fill="#fef08a" font-family="system-ui, sans-serif" font-size="22" font-weight="bold" letter-spacing="4" text-anchor="middle">CLERIC</text>
  <text x="256" y="465" fill="#eab308" font-family="system-ui, sans-serif" font-size="12" letter-spacing="2" text-anchor="middle">DIVINE HEALER</text>
</svg>""",

    "item_default.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <radialGradient id="bg-item" cx="50%" cy="45%" r="65%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#090d16"/>
    </radialGradient>
    <linearGradient id="chest-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#e2e8f0"/>
      <stop offset="100%" stop-color="#64748b"/>
    </linearGradient>
    <linearGradient id="gold-lock" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fde047"/>
      <stop offset="100%" stop-color="#ca8a04"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="32" fill="url(#bg-item)"/>
  <rect x="16" y="16" width="480" height="480" rx="24" fill="none" stroke="url(#chest-grad)" stroke-width="2" opacity="0.6"/>
  <!-- Treasure Chest / Box -->
  <path d="M 150 200 L 362 200 L 342 160 L 170 160 Z" fill="#475569" stroke="url(#gold-lock)" stroke-width="4"/>
  <rect x="140" y="200" width="232" height="140" rx="8" fill="#334155" stroke="url(#gold-lock)" stroke-width="4"/>
  <line x1="140" y1="230" x2="372" y2="230" stroke="url(#gold-lock)" stroke-width="3"/>
  <rect x="236" y="215" width="40" height="40" rx="6" fill="url(#gold-lock)"/>
  <circle cx="256" cy="232" r="5" fill="#0f172a"/>
  <text x="256" y="440" fill="#f8fafc" font-family="system-ui, sans-serif" font-size="22" font-weight="bold" letter-spacing="4" text-anchor="middle">ITEM</text>
  <text x="256" y="465" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="12" letter-spacing="2" text-anchor="middle">EQUIPMENT / INVENTORY</text>
</svg>""",

    "item_weapon.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <radialGradient id="bg-wpn" cx="50%" cy="45%" r="65%">
      <stop offset="0%" stop-color="#2a1810"/>
      <stop offset="100%" stop-color="#0a0503"/>
    </radialGradient>
    <linearGradient id="blade-metal" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="60%" stop-color="#94a3b8"/>
      <stop offset="100%" stop-color="#475569"/>
    </linearGradient>
    <linearGradient id="ember-glow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fb923c"/>
      <stop offset="100%" stop-color="#c2410c"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="32" fill="url(#bg-wpn)"/>
  <rect x="16" y="16" width="480" height="480" rx="24" fill="none" stroke="url(#ember-glow)" stroke-width="2" opacity="0.6"/>
  <!-- Longsword Diagonally -->
  <!-- Blade Tip to Guard -->
  <polygon points="360,110 375,125 250,290 235,275" fill="url(#blade-metal)" stroke="#f8fafc" stroke-width="2"/>
  <line x1="367" y1="117" x2="242" y2="282" stroke="#ea580c" stroke-width="2"/>
  <!-- Crossguard -->
  <line x1="200" y1="250" x2="270" y2="320" stroke="url(#ember-glow)" stroke-width="12" stroke-linecap="round"/>
  <!-- Grip and Pommel -->
  <line x1="225" y1="295" x2="175" y2="345" stroke="#78350f" stroke-width="8" stroke-linecap="round"/>
  <circle cx="165" cy="355" r="12" fill="url(#ember-glow)"/>
  <text x="256" y="440" fill="#fed7aa" font-family="system-ui, sans-serif" font-size="22" font-weight="bold" letter-spacing="4" text-anchor="middle">WEAPON</text>
  <text x="256" y="465" fill="#f97316" font-family="system-ui, sans-serif" font-size="12" letter-spacing="2" text-anchor="middle">COMBAT ARMS</text>
</svg>""",

    "item_armor.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <radialGradient id="bg-arm" cx="50%" cy="45%" r="65%">
      <stop offset="0%" stop-color="#141e28"/>
      <stop offset="100%" stop-color="#06090e"/>
    </radialGradient>
    <linearGradient id="plate-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#94a3b8"/>
      <stop offset="50%" stop-color="#64748b"/>
      <stop offset="100%" stop-color="#334155"/>
    </linearGradient>
    <linearGradient id="bronze-trim" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#0369a1"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="32" fill="url(#bg-arm)"/>
  <rect x="16" y="16" width="480" height="480" rx="24" fill="none" stroke="url(#bronze-trim)" stroke-width="2" opacity="0.6"/>
  <!-- Breastplate / Cuirass -->
  <path d="M 190 140 C 230 160, 282 160, 322 140 L 362 200 C 342 240, 332 300, 256 360 C 180 300, 170 240, 150 200 Z" fill="url(#plate-grad)" stroke="url(#bronze-trim)" stroke-width="4"/>
  <line x1="256" y1="160" x2="256" y2="355" stroke="url(#bronze-trim)" stroke-width="3"/>
  <text x="256" y="440" fill="#bae6fd" font-family="system-ui, sans-serif" font-size="22" font-weight="bold" letter-spacing="4" text-anchor="middle">ARMOR</text>
  <text x="256" y="465" fill="#38bdf8" font-family="system-ui, sans-serif" font-size="12" letter-spacing="2" text-anchor="middle">DEFENSIVE GEAR</text>
</svg>""",

    "item_potion.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <radialGradient id="bg-pot" cx="50%" cy="45%" r="65%">
      <stop offset="0%" stop-color="#2a0d1f"/>
      <stop offset="100%" stop-color="#0b0308"/>
    </radialGradient>
    <linearGradient id="potion-liq" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#f43f5e"/>
      <stop offset="100%" stop-color="#881337"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="32" fill="url(#bg-pot)"/>
  <rect x="16" y="16" width="480" height="480" rx="24" fill="none" stroke="#f43f5e" stroke-width="2" opacity="0.6"/>
  <!-- Flask Neck -->
  <rect x="236" y="140" width="40" height="60" rx="4" fill="#334155" stroke="#f43f5e" stroke-width="3"/>
  <!-- Cork -->
  <rect x="230" y="120" width="52" height="24" rx="4" fill="#d97706"/>
  <!-- Flask Body -->
  <circle cx="256" cy="270" r="85" fill="#1e1b4b" stroke="#f43f5e" stroke-width="4"/>
  <!-- Liquid -->
  <path d="M 180 290 Q 256 340 332 290 C 332 330 298 350 256 350 C 214 350 180 330 180 290 Z" fill="url(#potion-liq)"/>
  <circle cx="230" cy="280" r="8" fill="#fda4af" opacity="0.8"/>
  <circle cx="275" cy="295" r="5" fill="#fda4af" opacity="0.8"/>
  <text x="256" y="440" fill="#fecdd3" font-family="system-ui, sans-serif" font-size="22" font-weight="bold" letter-spacing="4" text-anchor="middle">POTION</text>
  <text x="256" y="465" fill="#fb7185" font-family="system-ui, sans-serif" font-size="12" letter-spacing="2" text-anchor="middle">CONSUMABLE ELIXIR</text>
</svg>""",

    "item_scroll.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <radialGradient id="bg-scr" cx="50%" cy="45%" r="65%">
      <stop offset="0%" stop-color="#272213"/>
      <stop offset="100%" stop-color="#0d0b06"/>
    </radialGradient>
    <linearGradient id="parchment" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fef3c7"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="32" fill="url(#bg-scr)"/>
  <rect x="16" y="16" width="480" height="480" rx="24" fill="none" stroke="#f59e0b" stroke-width="2" opacity="0.6"/>
  <!-- Rolled Scroll -->
  <rect x="170" y="160" width="172" height="190" rx="8" fill="url(#parchment)"/>
  <ellipse cx="256" cy="160" rx="86" ry="16" fill="#fef9c3" stroke="#b45309" stroke-width="2"/>
  <ellipse cx="256" cy="350" rx="86" ry="16" fill="#b45309" stroke="#78350f" stroke-width="2"/>
  <!-- Ribbon & Seal -->
  <line x1="170" y1="250" x2="342" y2="250" stroke="#b91c1c" stroke-width="10"/>
  <circle cx="256" cy="250" r="20" fill="#dc2626" stroke="#fca5a5" stroke-width="3"/>
  <text x="256" y="440" fill="#fef3c7" font-family="system-ui, sans-serif" font-size="22" font-weight="bold" letter-spacing="4" text-anchor="middle">SCROLL</text>
  <text x="256" y="465" fill="#f59e0b" font-family="system-ui, sans-serif" font-size="12" letter-spacing="2" text-anchor="middle">MAGIC PARCHMENT</text>
</svg>""",

    "scene_default.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="100%" height="100%">
  <defs>
    <linearGradient id="sky-grad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="60%" stop-color="#1e1b4b"/>
      <stop offset="100%" stop-color="#311042"/>
    </linearGradient>
    <linearGradient id="mountain-grad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#090d16"/>
    </linearGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#sky-grad)"/>
  <!-- Distant Mountains -->
  <polygon points="0,520 280,340 540,500 850,300 1150,530 1280,480 1280,720 0,720" fill="url(#mountain-grad)"/>
  <!-- Moon / Gateway -->
  <circle cx="850" cy="220" r="70" fill="#f8fafc" opacity="0.8"/>
  <circle cx="830" cy="210" r="60" fill="#1e1b4b" opacity="0.5"/>
  <!-- Ground Foreground -->
  <path d="M 0 580 Q 320 540 640 590 T 1280 570 L 1280 720 L 0 720 Z" fill="#020617"/>
  <rect x="24" y="24" width="1232" height="672" rx="16" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="2"/>
  <text x="640" y="640" fill="#f8fafc" font-family="system-ui, sans-serif" font-size="32" font-weight="bold" letter-spacing="6" text-anchor="middle">SCENE NARRATIVE</text>
  <text x="640" y="675" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="16" letter-spacing="3" text-anchor="middle">ATMOSPHERIC ENVIRONMENT</text>
</svg>""",

    "scene_tavern.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="100%" height="100%">
  <defs>
    <radialGradient id="hearth-glow" cx="50%" cy="60%" r="70%">
      <stop offset="0%" stop-color="#78350f"/>
      <stop offset="50%" stop-color="#2d1506"/>
      <stop offset="100%" stop-color="#0d0502"/>
    </radialGradient>
    <linearGradient id="fire" x1="0%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="#ea580c"/>
      <stop offset="50%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#fef08a"/>
    </linearGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#hearth-glow)"/>
  <!-- Beams -->
  <rect x="100" y="0" width="60" height="720" fill="#1c0c04"/>
  <rect x="1120" y="0" width="60" height="720" fill="#1c0c04"/>
  <rect x="0" y="60" width="1280" height="40" fill="#2d1506"/>
  <!-- Fireplace Hearth -->
  <path d="M 520 420 Q 640 320 760 420 L 780 620 L 500 620 Z" fill="#1c1917" stroke="#78350f" stroke-width="6"/>
  <!-- Flame -->
  <polygon points="640,420 670,540 640,520 610,540" fill="url(#fire)"/>
  <!-- Hearth Fire Glow -->
  <circle cx="640" cy="490" r="40" fill="#f59e0b" opacity="0.4"/>
  <rect x="24" y="24" width="1232" height="672" rx="16" fill="none" stroke="rgba(245,158,11,0.25)" stroke-width="2"/>
  <text x="640" y="650" fill="#fef3c7" font-family="system-ui, sans-serif" font-size="32" font-weight="bold" letter-spacing="6" text-anchor="middle">THE RUSTIC TAVERN</text>
  <text x="640" y="685" fill="#f59e0b" font-family="system-ui, sans-serif" font-size="16" letter-spacing="3" text-anchor="middle">PEACEFUL HAVEN / RESTING COMMONS</text>
</svg>""",

    "scene_dungeon.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="100%" height="100%">
  <defs>
    <radialGradient id="dungeon-dark" cx="50%" cy="50%" r="65%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="60%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#020617"/>
    </radialGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#dungeon-dark)"/>
  <!-- Stone Vault Arch -->
  <path d="M 280 720 L 280 340 C 280 180, 1000 180, 1000 340 L 1000 720" fill="none" stroke="#334155" stroke-width="32"/>
  <path d="M 380 720 L 380 380 C 380 260, 900 260, 900 380 L 900 720" fill="none" stroke="#1e293b" stroke-width="24"/>
  <!-- Iron Portcullis Bars -->
  <line x1="560" y1="310" x2="560" y2="720" stroke="#0f172a" stroke-width="12"/>
  <line x1="640" y1="300" x2="640" y2="720" stroke="#0f172a" stroke-width="12"/>
  <line x1="720" y1="310" x2="720" y2="720" stroke="#0f172a" stroke-width="12"/>
  <!-- Torches -->
  <circle cx="230" cy="360" r="14" fill="#f97316"/>
  <circle cx="1050" cy="360" r="14" fill="#f97316"/>
  <rect x="24" y="24" width="1232" height="672" rx="16" fill="none" stroke="rgba(148,163,184,0.2)" stroke-width="2"/>
  <text x="640" y="650" fill="#e2e8f0" font-family="system-ui, sans-serif" font-size="32" font-weight="bold" letter-spacing="6" text-anchor="middle">SUBTERRANEAN DUNGEON</text>
  <text x="640" y="685" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="16" letter-spacing="3" text-anchor="middle">ANCIENT CRYPT / PERILOUS LABYRINTH</text>
</svg>""",

    "scene_wilderness.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="100%" height="100%">
  <defs>
    <linearGradient id="wild-sky" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#022c22"/>
      <stop offset="60%" stop-color="#064e3b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#wild-sky)"/>
  <!-- Moon -->
  <circle cx="960" cy="180" r="50" fill="#a7f3d0" opacity="0.9"/>
  <!-- Pine Trees Silhouette -->
  <polygon points="180,620 120,440 240,620" fill="#021a14"/>
  <polygon points="260,630 200,410 320,630" fill="#04271e"/>
  <polygon points="400,640 330,380 470,640" fill="#021a14"/>
  <polygon points="820,620 760,400 880,620" fill="#021a14"/>
  <polygon points="1020,630 950,360 1090,630" fill="#04271e"/>
  <!-- Ground -->
  <rect x="0" y="600" width="1280" height="120" fill="#01110d"/>
  <rect x="24" y="24" width="1232" height="672" rx="16" fill="none" stroke="rgba(52,211,153,0.2)" stroke-width="2"/>
  <text x="640" y="650" fill="#d1fae5" font-family="system-ui, sans-serif" font-size="32" font-weight="bold" letter-spacing="6" text-anchor="middle">ENCHANTED WILDERNESS</text>
  <text x="640" y="685" fill="#34d399" font-family="system-ui, sans-serif" font-size="16" letter-spacing="3" text-anchor="middle">PRIMEVAL WOODS / UNCHARTED REALM</text>
</svg>""",

    "battlemap_default.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="100%" height="100%">
  <defs>
    <radialGradient id="map-bg" cx="50%" cy="50%" r="70%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#090d16"/>
    </radialGradient>
    <pattern id="grid-pattern" width="80" height="80" patternUnits="userSpaceOnUse">
      <rect width="80" height="80" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="1.5"/>
      <circle cx="40" cy="40" r="1.5" fill="rgba(255,255,255,0.25)"/>
    </pattern>
  </defs>
  <rect width="800" height="800" fill="url(#map-bg)"/>
  <rect width="800" height="800" fill="url(#grid-pattern)"/>
  <!-- Border and Coordinate Markers -->
  <rect x="8" y="8" width="784" height="784" rx="12" fill="none" stroke="#64748b" stroke-width="3"/>
  <!-- Compass Rose -->
  <g transform="translate(730, 70)" opacity="0.6">
    <circle cx="0" cy="0" r="30" fill="none" stroke="#94a3b8" stroke-width="1.5"/>
    <polygon points="0,-24 6,-6 0,0 -6,-6" fill="#f87171"/>
    <polygon points="0,24 6,6 0,0 -6,6" fill="#94a3b8"/>
    <text x="0" y="-28" fill="#f87171" font-size="12" font-family="sans-serif" font-weight="bold" text-anchor="middle">N</text>
  </g>
  <text x="400" y="405" fill="rgba(255,255,255,0.08)" font-family="system-ui, sans-serif" font-size="64" font-weight="bold" letter-spacing="12" text-anchor="middle">TACTICAL GRID</text>
  <text x="400" y="770" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="14" font-weight="bold" letter-spacing="4" text-anchor="middle">10 x 10 BATTLEFIELD MAP</text>
</svg>""",

    "battlemap_stone.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="100%" height="100%">
  <defs>
    <radialGradient id="stone-bg" cx="50%" cy="50%" r="65%">
      <stop offset="0%" stop-color="#334155"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </radialGradient>
    <pattern id="flagstone-grid" width="80" height="80" patternUnits="userSpaceOnUse">
      <rect x="2" y="2" width="76" height="76" rx="4" fill="#1e293b" stroke="#475569" stroke-width="1.5"/>
      <line x1="10" y1="20" x2="40" y2="25" stroke="#334155" stroke-width="1"/>
      <line x1="50" y1="60" x2="70" y2="55" stroke="#334155" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="800" height="800" fill="url(#stone-bg)"/>
  <rect width="800" height="800" fill="url(#flagstone-grid)"/>
  <rect x="8" y="8" width="784" height="784" rx="12" fill="none" stroke="#94a3b8" stroke-width="3"/>
  <text x="400" y="405" fill="rgba(255,255,255,0.07)" font-family="system-ui, sans-serif" font-size="54" font-weight="bold" letter-spacing="10" text-anchor="middle">STONE DUNGEON</text>
  <text x="400" y="770" fill="#cbd5e1" font-family="system-ui, sans-serif" font-size="14" font-weight="bold" letter-spacing="4" text-anchor="middle">FLAGSTONE CHAMBER (10x10)</text>
</svg>""",

    "battlemap_dungeon.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="100%" height="100%">
  <defs>
    <radialGradient id="dungeon-bg" cx="50%" cy="50%" r="70%">
      <stop offset="0%" stop-color="#18181b"/>
      <stop offset="100%" stop-color="#09090b"/>
    </radialGradient>
    <pattern id="dungeon-grid" width="80" height="80" patternUnits="userSpaceOnUse">
      <rect width="80" height="80" fill="none" stroke="rgba(255,255,255,0.14)" stroke-width="1.5"/>
    </pattern>
  </defs>
  <rect width="800" height="800" fill="url(#dungeon-bg)"/>
  <rect width="800" height="800" fill="url(#dungeon-grid)"/>
  <!-- Dungeon Walls / Obstacles -->
  <rect x="0" y="0" width="80" height="800" fill="#27272a"/>
  <rect x="720" y="0" width="80" height="800" fill="#27272a"/>
  <rect x="0" y="0" width="800" height="80" fill="#27272a"/>
  <rect x="0" y="720" width="800" height="80" fill="#27272a"/>
  <!-- Pillars -->
  <rect x="240" y="240" width="80" height="80" rx="8" fill="#3f3f46" stroke="#71717a" stroke-width="2"/>
  <rect x="480" y="240" width="80" height="80" rx="8" fill="#3f3f46" stroke="#71717a" stroke-width="2"/>
  <rect x="240" y="480" width="80" height="80" rx="8" fill="#3f3f46" stroke="#71717a" stroke-width="2"/>
  <rect x="480" y="480" width="80" height="80" rx="8" fill="#3f3f46" stroke="#71717a" stroke-width="2"/>
  <text x="400" y="405" fill="rgba(255,255,255,0.06)" font-family="system-ui, sans-serif" font-size="52" font-weight="bold" letter-spacing="8" text-anchor="middle">PILLARED HALL</text>
  <text x="400" y="760" fill="#a1a1aa" font-family="system-ui, sans-serif" font-size="14" font-weight="bold" letter-spacing="4" text-anchor="middle">TACTICAL DUNGEON ARENA</text>
</svg>""",

    "battlemap_wilderness.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="100%" height="100%">
  <defs>
    <radialGradient id="wild-bg" cx="50%" cy="50%" r="70%">
      <stop offset="0%" stop-color="#14532d"/>
      <stop offset="100%" stop-color="#052e16"/>
    </radialGradient>
    <pattern id="wild-grid" width="80" height="80" patternUnits="userSpaceOnUse">
      <rect width="80" height="80" fill="none" stroke="rgba(255,255,255,0.18)" stroke-width="1.5"/>
    </pattern>
  </defs>
  <rect width="800" height="800" fill="url(#wild-bg)"/>
  <!-- River/Path traversing the map -->
  <path d="M 0 320 Q 240 400 400 360 T 800 440 L 800 520 Q 480 440 320 480 T 0 400 Z" fill="#0369a1" opacity="0.6"/>
  <rect width="800" height="800" fill="url(#wild-grid)"/>
  <rect x="8" y="8" width="784" height="784" rx="12" fill="none" stroke="#22c55e" stroke-width="3" opacity="0.6"/>
  <text x="400" y="405" fill="rgba(255,255,255,0.07)" font-family="system-ui, sans-serif" font-size="52" font-weight="bold" letter-spacing="8" text-anchor="middle">RIVER CROSSING</text>
  <text x="400" y="770" fill="#86efac" font-family="system-ui, sans-serif" font-size="14" font-weight="bold" letter-spacing="4" text-anchor="middle">WILDERNESS GLADE (10x10)</text>
</svg>"""
}
