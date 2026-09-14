import os
import subprocess
import time
import xml.etree.ElementTree as ET

# URL de jsdelivr para "updatepkg": confirmado en juego, varias veces, que
# "@main/Petria-Rhuna.xml" (rama mutable) es poco confiable -- ya sea por
# cache (CDN o del cliente Qt de Mudlet) o por algo en como Mudlet maneja
# la descarga, quedaba trayendo versiones viejas o fallando en silencio.
# Un "?v=<timestamp>" para forzar cache-busting tambien fallo (Mudlet no
# bajaba el paquete con esa url en mas de un intento). LO UNICO que
# funciono siempre, sin excepcion, fue instalar desde un COMMIT EXACTO
# (@<sha>/Petria-Rhuna.xml, sin query string) -- un commit ya empujado a
# GitHub es contenido inmutable, jsdelivr lo sirve sin ambiguedad de cache
# apenas existe. Por eso "updatepkg" apunta al commit HEAD *previo* a este
# build (obtenido con "git rev-parse HEAD" antes de generar el archivo):
# ese commit ya esta pusheado y ya tiene todo el contenido funcional de
# este build salvo, como mucho, el numero de commit al que apunta esta
# misma linea -- nunca al codigo real (triggers/alias/scripts). El
# workflow de publicacion hace un segundo commit chico despues de este
# para "clavar" la url al commit recien creado (ver mensajes de build).
try:
    JSDELIVR_PIN_COMMIT = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=os.path.dirname(os.path.abspath(__file__))
    ).decode().strip()
except Exception:
    JSDELIVR_PIN_COMMIT = "main"
JSDELIVR_URL = f"https://cdn.jsdelivr.net/gh/z0y1b0t/petria-mudlet@{JSDELIVR_PIN_COMMIT}/Petria-Rhuna.xml"
JSDELIVR_CACHE_BUSTER = int(time.time())  # usado solo para Petria.version ("updatepkg -v")

def indent(elem, level=0):
    i = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

root = ET.Element("MudletPackage", {"version": "1.001"})

def make_trigger_group(parent, name):
    g = ET.SubElement(parent, "TriggerGroup", {
        "isActive": "yes", "isFolder": "yes", "isTempTrigger": "no", "isMultiline": "no",
        "isPerlSlashGOption": "no", "isColorizerTrigger": "no", "isFilterTrigger": "no",
        "isSoundTrigger": "no", "isColorTrigger": "no", "isColorTriggerFg": "no", "isColorTriggerBg": "no",
    })
    ET.SubElement(g, "name").text = name
    ET.SubElement(g, "script").text = ""
    ET.SubElement(g, "triggerType").text = "0"
    ET.SubElement(g, "conditonLineDelta").text = "0"
    ET.SubElement(g, "mStayOpen").text = "0"
    ET.SubElement(g, "mCommand").text = ""
    ET.SubElement(g, "packageName").text = ""
    ET.SubElement(g, "mFgColor").text = "#ff0000"
    ET.SubElement(g, "mBgColor").text = "#ffff00"
    ET.SubElement(g, "mSoundFile").text = ""
    ET.SubElement(g, "colorTriggerFgColor").text = "#000000"
    ET.SubElement(g, "colorTriggerBgColor").text = "#000000"
    ET.SubElement(g, "regexCodeList")
    ET.SubElement(g, "regexCodePropertyList")
    return g

# ---------- TriggerPackage ----------
# Clases ya no usa triggers de texto: la clase llega por GMCP (ver ScriptPackage).
trig_pkg = ET.SubElement(root, "TriggerPackage")

def make_trigger(parent, name, script, patterns):
    """patterns: list of (regex, propertyType) propertyType 1=substring? here we use regex(1)"""
    attrs = {
        "isActive": "yes", "isFolder": "no", "isTempTrigger": "no", "isMultiline": "no",
        "isPerlSlashGOption": "no", "isColorizerTrigger": "no", "isFilterTrigger": "no",
        "isSoundTrigger": "no", "isColorTrigger": "no", "isColorTriggerFg": "no", "isColorTriggerBg": "no",
    }
    t = ET.SubElement(parent, "Trigger", attrs)
    ET.SubElement(t, "name").text = name
    ET.SubElement(t, "script").text = script
    ET.SubElement(t, "triggerType").text = "0"
    ET.SubElement(t, "conditonLineDelta").text = "0"
    ET.SubElement(t, "mStayOpen").text = "0"
    ET.SubElement(t, "mCommand").text = ""
    ET.SubElement(t, "packageName").text = ""
    ET.SubElement(t, "mFgColor").text = "#ff0000"
    ET.SubElement(t, "mBgColor").text = "#ffff00"
    ET.SubElement(t, "mSoundFile").text = ""
    ET.SubElement(t, "colorTriggerFgColor").text = "#000000"
    ET.SubElement(t, "colorTriggerBgColor").text = "#000000"
    rcl = ET.SubElement(t, "regexCodeList")
    rcp = ET.SubElement(t, "regexCodePropertyList")
    for pat in patterns:
        ET.SubElement(rcl, "string").text = pat
        ET.SubElement(rcp, "integer").text = "1"  # 1 = perl regex
    return t

petria_trig_group = make_trigger_group(trig_pkg, "Petria-Rhuna")
pelea_trig_group = make_trigger_group(petria_trig_group, "Pelea")

# --- Autodope: recastea buffs propios apenas se van despejando ---
# Asociado a mano contra la lista de "spells" del personaje (seguidores_de
# Oteren) + los mensajes de "se te pasa el efecto" que se ven en juego.
# "Comienzas a descongelarte." quedo afuera: no matchea con nada de la
# lista de spells (podria ser el fin de un efecto hostil, no un buff propio
# para recastear) -- confirmar antes de agregarlo.
autodope_trig_group = make_trigger_group(petria_trig_group, "Autodope")
make_trigger(autodope_trig_group, "Santuario se despeja", 'send("c santuario")', [r"^Los efectos de Santuario se van despejando\.$"])
make_trigger(autodope_trig_group, "Inspiracion divina se va", 'send("c inspiracion")', [r"^Sientes como tu inspiracion divina te abandona\.\.\.$"])
make_trigger(autodope_trig_group, "Fuerza colosal se va (mas debil)", 'send("c \'fuerza colosal\'")', [r"^Te sientes mas debil\.$"])
make_trigger(autodope_trig_group, "Proteccion infernal mengua", 'send("c \'proteccion infernal\'")', [r"^Tu proteccion contra el mal mengua\.$"])
make_trigger(autodope_trig_group, "Escudo de luz desaparece", 'send("c \'escudo luz\'")', [r"^El escudo de luz que te rodeaba desaparece\.$"])
make_trigger(autodope_trig_group, "Luz protectora desaparece", 'send("c \'luz protectora\'")', [r"^Los rayos de luz que te rodeaban desaparecen\.$"])
make_trigger(autodope_trig_group, "Proteccion sagrada se desvanece", 'send("c \'proteccion sagrada\'")', [r"^Tu proteccion sagrada se desvanece"])
make_trigger(autodope_trig_group, "Acelerar termina (ritmo normal)", 'send("c acelerar")', [r"^Ya vuelves a recuperar tu ritmo normal\.$"])
make_trigger(autodope_trig_group, "Volar termina", 'send("c volar")', [r"^Despacito dejas de levitar como un Lama tibetano\.$"])
make_trigger(autodope_trig_group, "Bendecir termina", 'send("c bendecir")', [r"^La bendicion ya no tiene efecto\.$"])
make_trigger(
    autodope_trig_group, "Menos cansado: seguir curando hasta llenar move",
    '-- Intencional: "curar refre" tirado a mano dispara al curandero, y\n'
    '-- cada cura da un poco de move (ej. "[+180 move]"). Repetir hasta\n'
    '-- llenar el move (gmcp.Char.Vitals) en vez de solo una vez, para no\n'
    '-- quedar pidiendo cura para siempre despues de estar lleno.\n'
    'local move = gmcp and gmcp.Char and gmcp.Char.Vitals and tonumber(gmcp.Char.Vitals.move)\n'
    'local maxmove = gmcp and gmcp.Char and gmcp.Char.Vitals and tonumber(gmcp.Char.Vitals.maxmove)\n'
    'if not move or not maxmove or move < maxmove then\n'
    '  send("curar refre")\n'
    'end',
    [r"Te sientes menos cansado\."],
)

# --- Auto-heal por %HP ---
# El patron original en CMUD (03-Pelea) esta corrupto/desactualizado en el
# export. El auto-heal y el tracking de enemigo YA NO usan texto: se
# reemplazaron por gmcp.Char.Vitals y gmcp.Char.Enemies (ver ScriptPackage,
# funcion PeleaActualizarVitalsGMCP / PeleaActualizarEnemigoGMCP). Mucho mas
# confiable que parsear el prompt.
make_trigger(
    pelea_trig_group, "Fin de combate: enemigo muerto",
    'en_combate = 0\npcall(function() Pelea.cancelarTimersPendientes() end)',
    [r"ESTA MUERTO !!$"],
)
make_trigger(
    pelea_trig_group, "Fin de combate: huida",
    'en_combate = 0\npcall(function() Pelea.cancelarTimersPendientes() end)',
    [r"Logras HUIR!"],
)

make_trigger(
    pelea_trig_group, "Hechizo fallado: reintentar",
    'if en_combate and en_combate ~= 0 and ultima_skill and ultima_skill ~= "" then\n'
    '  expandAlias(ultima_skill)\n'
    'end',
    [r"^Hechizo fallado\.$"],
)
make_trigger(
    pelea_trig_group, "Cooldown tormenta prismatica",
    'if en_combate and en_combate ~= 0 then send("c torme") end',
    [r"^El cooldown de tormenta prismatica ha terminado\.$"],
)
make_trigger(
    pelea_trig_group, "Cooldown diluvio acido",
    'if en_combate and en_combate ~= 0 then send("c dilu") end',
    [r"^El cooldown de diluvio acido ha terminado\.$"],
)
make_trigger(
    pelea_trig_group, "Post-kill: loot y reset de aliento",
    'send("GET ALEA")\n'
    'send("exam cu")\n'
    'send("lo")\n'
    'ResetAliento()\n'
    'pcall(enableTriggerGroup, "GA01")\n'
    'ultima_skill = ""',
    [r"ESTA MUERTO !!$"],
)
# Objetos que empiezan con "(LEGENDARIO)" en el contenido del cadaver (se ve
# con "lo"/"exam cu", que el trigger de arriba ya dispara). Confirmado en
# juego: "(LEGENDARIO)" es solo una etiqueta de rareza, NO es una palabra
# clave valida para "coger" (ni "legendario" ni el prefijo "legendari"
# funcionan) -- y hay cientos de objetos, cada uno con nombre distinto,
# asi que no hay una sola palabra fija que sirva siempre. En vez de eso: se
# saca el texto entre parentesis (todas las etiquetas, no solo LEGENDARIO),
# y se usa la primera palabra significativa del nombre que queda (saltando
# articulos) como palabra clave. Ej. "(LEGENDARIO) (Magico) una Calabaza
# Legendaria" -> "Calabaza". Es una heuristica, no esta 100% garantizado
# que el juego indexe justo esa palabra -- probar con varios objetos
# distintos y avisar si alguno no se agarra.
make_trigger(
    pelea_trig_group, "Objeto legendario en cadaver",
    '''local linea = matches[1]
local nombre = linea:gsub("%b()", "")
nombre = nombre:gsub("^%s+", ""):gsub("%s+$", "")

local palabrasChicas = {
  un = true, una = true, unos = true, unas = true,
  el = true, la = true, los = true, las = true,
  de = true, del = true, y = true,
}

local palabraClave = nil
for palabra in nombre:gmatch("%a+") do
  if not palabrasChicas[palabra:lower()] then
    palabraClave = palabra:lower()
    break
  end
end

if palabraClave then
  send("coger " .. palabraClave)
end''',
    [r"^\s*\(LEGENDARIO\)"],
)
make_trigger(
    pelea_trig_group, "Presencia enemiga en la sombra",
    'send("k " .. matches[2])',
    [r"Sientes la presencia de un (\w+) en la sombra\."],
)
make_trigger(
    pelea_trig_group, "Cooldown chupar energia",
    'if en_combate and en_combate ~= 0 then send("c chupar") end',
    [r"El cooldown de chupar energia ha terminado\."],
)
make_trigger(
    pelea_trig_group, "Reintentar skill tras fallo",
    'if en_combate and en_combate ~= 0 and ultima_skill and ultima_skill ~= "" then\n'
    '  expandAlias(ultima_skill)\n'
    'end',
    [r"^Has fallado\.$"],
)
make_trigger(
    pelea_trig_group, "Sin mana: recall",
    '-- No insistir con recall si ya sabemos que esta bloqueado en esta zona\n'
    '-- (ver trigger "Recall fallido: los dioses te han olvidado").\n'
    'if recallBloqueado then return end\n'
    'send("recall")\n'
    'tempTimer(1, function() send("n") end)',
    [r"No tienes suficiente mana\.$"],
)
make_trigger(
    pelea_trig_group, "Recall fallido: los dioses te han olvidado",
    '-- Confirmado en juego: esto pasa en zonas (NO RECALL) y el recall NUNCA\n'
    '-- va a funcionar ahi por mas que se reintente. Antes se quedaba\n'
    '-- reintentando "recall" a ciegas cientos de veces sin exito.\n'
    'recallBloqueado = true\n'
    'tempTimer(15, function() recallBloqueado = false end)\n'
    'pcall(function() Pelea.cancelarTimersPendientes() end)\n'
    'Pelea.alerta("RECALL BLOQUEADO en esta zona - movete a mano")',
    [r"^Los Dioses te han olvidado\.$"],
)
make_trigger(
    pelea_trig_group, "Alerta: ataque de jugador (PK)",
    '-- "Someone" aparece cuando NO podes ver/detectar a quien te ataca (no\n'
    '-- es exclusivo de PK, es "no identificado") -- pero reaccionar igual\n'
    '-- tiene sentido ante algo no identificado. Confirmado en juego que\n'
    '-- "Someone" sirve como objetivo real para comandos de ataque (tus\n'
    '-- propios golpes tambien se describen como "a Someone").\n'
    '-- NO se manda "can Someone" (cancelacion): si "Someone" no es target\n'
    '-- valido para ese hechizo especifico, puede no encontrar objetivo y\n'
    '-- terminar cancelando tus propios buffs -- riesgo peor que no cancelar\n'
    '-- nada. Confirmar la sintaxis correcta antes de automatizarlo.\n'
    '-- Consejo de Santana: "si ya inicio la pelea recupera santuario y\n'
    '-- volar" -- los recasta si Char.Affects.BuffYDebuff dice que no los\n'
    '-- tenes activos (confirmado en juego que ambos se pueden despejar en\n'
    '-- medio de un PK real).\n'
    'Pelea.alerta("TE ATACA UN JUGADOR (Someone) -- contraatacando")\n'
    'if not Clases.tieneActivo("santuario") then send("c santuario") end\n'
    'if not Clases.tieneActivo("volar") then send("c volar") end\n'
    'expandAlias("k Someone")',
    [r"^Someone empieza a atacarte\.$"],
)
make_trigger(
    pelea_trig_group, "Alerta de Vigia: enemigo va a mi area",
    '-- Los vigias del clan avisan cuando un enemigo entra a un area, ej.:\n'
    '-- "[Alerta](Vigia Explorador) Arikel --> detecta presencia enemiga:\n'
    '-- Alien en El Olimpo". Si el area coincide con la actual\n'
    '-- (gmcp.Room.Info.area, confirmado que existe con "lua display(gmcp)"),\n'
    '-- alerta fuerte + corre "rango" para ver quien anda cerca de verdad.\n'
    'local vigia, enemigo, area = matches[2], matches[3], matches[4]\n'
    'local areaActual = gmcp and gmcp.Room and gmcp.Room.Info and gmcp.Room.Info.area\n'
    'if areaActual and area:lower() == areaActual:lower() then\n'
    '  Pelea.alerta(string.format("%s DETECTADO EN TU AREA (%s) -- avisa %s", enemigo, area, vigia))\n'
    '  send("rango")\n'
    'end',
    [r"\[Alerta\]\(Vigia [^)]+\) (\w+) --> detecta presencia enemiga: (.+) en (.+)$"],
)
make_trigger(
    pelea_trig_group, "Garganta degollada: pausar pociones",
    '-- Confirmado en juego: con la garganta degollada, tomar una pocion\n'
    '-- EMPEORA la herida ("tu garganta degollada se abre causando X heridas\n'
    '-- mas"). El auto-heal (PeleaActualizarVitalsGMCP) chequea este flag\n'
    '-- antes de mandar "traga sa" para no seguir lastimandote solo.\n'
    'gargantaCortada = true\n'
    'tempTimer(20, function() gargantaCortada = false end)\n'
    'Pelea.alerta("GARGANTA DEGOLLADA -- las pociones empeoran, curar de otra forma")',
    [r"tu garganta degollada se abre"],
)
make_trigger(
    pelea_trig_group, "Poder magico revitalizado: continuar",
    'if ir_Obj and ir_Obj ~= "" then send("ir " .. ir_Obj) end\n'
    'if rasOBJ and rasOBJ ~= "" then send("ras " .. rasOBJ) end',
    [r"Sientes totalmente revitalizado tu poder mágico\."],
)
make_trigger(
    pelea_trig_group, "Muy cansado para rastrear",
    'send("get melon moch")\n'
    'send("comer melon")\n'
    'if rasOBJ and rasOBJ ~= "" then send("ras " .. rasOBJ) end',
    [r"¡?Estás demasiado cansado para rastrear!$"],
)
# (?i) case-insensitive + [aA\xe1\xc1] tolera "a"/"A"/"á"/"Á": confirmado en
# juego (pelea contra El Rey Blanco) que el patron viejo "ESTaS" (a suelta,
# de una version con encoding roto de antes) NUNCA matcheaba el texto real
# "ESTÁS" -- la cura de emergencia por sangrado nunca disparo en toda esa
# pelea, justo cuando mas hacia falta.
make_trigger(pelea_trig_group, "Sangrado fuerte: huir", 'send("huir")', [r"(?i)¡?¡?SANGR[aáA]S A LO BESTIA!!"])
make_trigger(pelea_trig_group, "Perdiendo mucha sangre: curar", 'send("traga sana")', [r"(?i)¡?¡?EST[aáA]S PERDIENDO DEMASIADA SANGRE!!"])
make_trigger(
    pelea_trig_group, "Demasiado cansado: refrescar",
    'send("c refrescar")\nsend("c refrescar")\nsend("c refrescar")',
    [r"^Estas demasiado cansado\.$"],
)
make_trigger(
    pelea_trig_group, "Escudo de hielo se disuelve",
    'send("c \'escudo de hielo\'")',
    [r"^El escudo de hielo se disuelve en el ambiente\.$"],
)
make_trigger(pelea_trig_group, "Debilidad Luz termina", "ResetAliento()", [r"^La Debilidad Luz deja de afectar"])
make_trigger(
    pelea_trig_group, "Debilidad Rayo termina",
    'ResetAliento()\nsend("c \'debilidad rayo\'")',
    [r"^La Debilidad Rayo deja de afectar"],
)
make_trigger(
    pelea_trig_group, "Debilidad Acida termina",
    'send("c \'debilidad acida\'")',
    [r"^La Debilidad Acida deja de afectar a"],
)
make_trigger(
    pelea_trig_group, "Cooldown golpe acido",
    'Pelea.programarSiEnCombate(4, function()\n'
    '  if not qcomm or qcomm <= 2 then send("c golpe") end\n'
    'end)',
    [r"^Tu golpe acido hace"],
)
make_trigger(
    pelea_trig_group, "Fuente arcana seca",
    'send("fuen")\nsend("bebe")',
    [r"^Una fuente arcana se seca\.$"],
)
make_trigger(
    pelea_trig_group, "Cooldown rayo (aliento)",
    'Pelea.programarSiEnCombate(2, function() send("rp") end)',
    [r"^Tu poderoso rayo"],
)
make_trigger(
    pelea_trig_group, "Inmune a golpe acido",
    'pcall(disableTriggerGroup, "GA01")',
    [r"es inmune a tu golpe acido!"],
)
make_trigger(
    pelea_trig_group, "Cooldown aliento tormentoso",
    'Pelea.programarSiEnCombate(5, function() send("c \'aliento tormentoso\'") end)',
    [r"^Escupes un tremendo rayo"],
)
make_trigger(
    pelea_trig_group, "Deslumbrado: curar ceguera",
    '-- "curar deslumbrar" es hechizo (no depende de pociones limitadas,\n'
    '-- que ya vimos que se pueden acabar en medio de una pelea). Se manda\n'
    '-- junto con la pocion, lo que responda primero cura.\n'
    'send("c \'curar deslumbrar\'")\n'
    'send("traga ceguera")',
    [r"^\.\.Has sido deslumbrado!!$"],
)
make_trigger(
    pelea_trig_group, "Tracker de qcomm (linea de estado)",
    "qcomm = tonumber(matches[3])",
    [r"^\|(.*)\[(\d+)\]\s*(.*)G"],
)
make_trigger(pelea_trig_group, "Enemigo deslumbrado: curar", 'send("c \'curar deslumbrar\'")', [r"ha sido deslumbrado!!$"])
make_trigger(pelea_trig_group, "Raices resistidas: reintentar", 'send("c raices")', [r"Haces brotar ra.ces del suelo, pero (.*) se resiste a ellas\.$"])
make_trigger(
    pelea_trig_group, "Guardia del puente",
    'if not cd_guardia or cd_guardia == 0 then\n'
    '  send("vis")\n'
    '  send("decir puedo entrar?")\n'
    '  cd_guardia = 1\n'
    '  tempTimer(10, function() cd_guardia = 0 end)\n'
    'end',
    [r"^\(Malo\) El guardia del puente vigila el acceso\."],
)
make_trigger(
    pelea_trig_group, "Envenenado: curar",
    'if not cd_veneno or cd_veneno == 0 then\n'
    '  send(\'c "curar veneno"\')\n'
    '  send("curar veneno"); send("curar veneno"); send("curar veneno")\n'
    '  cd_veneno = 1\n'
    '  tempTimer(6, function() cd_veneno = 0 end)\n'
    'end',
    [r"Tienes retortijones y vomitas\."],
)
make_trigger(pelea_trig_group, "Recuperado de golpetazo", 'expandAlias("skill golpeta")', [r"se recupera de los efectos del golpetazo\.$"])
make_trigger(pelea_trig_group, "Transeunte resiste raices", 'send("c rai")', [r"pero un transeunte casual se resiste a ellas\.$"])
make_trigger(pelea_trig_group, "Cegados por suciedad: zancadilla", 'expandAlias("skill zancadilla")', [r"han sido cegados por la suciedad!"])
# Enemigo (PvE normal, no WoF/PK) huye de la pelea: lo perseguimos y
# reatacamos, en vez de dejarlo escapar. Igual patron que "Amigo WoF se va
# por una salida" (linea de abajo, esa es solo para WoFriends) pero
# generico -- se dispara si el nombre completo de quien huye (matches[2])
# contiene el keyword que le pasamos a "k"/"kk" (rasOBJ), asi no persigue
# a cualquiera que huya en la sala, solo al objetivo actual.
make_trigger(
    pelea_trig_group, "Enemigo huye: perseguir y reatacar",
    'local nombreCompleto, direccion = matches[2], matches[3]\n'
    'if rasOBJ and rasOBJ ~= "" and nombreCompleto:lower():find(rasOBJ:lower(), 1, true) then\n'
    '  send(direccion)\n'
    '  send("k " .. rasOBJ)\n'
    'end',
    [r"^(.+) se va por el (\w+)\.$"],
)
make_trigger(
    pelea_trig_group, "Defensa expuesta: rodear o corte artero",
    'local pct = tonumber(matches[2]) or 0\n'
    'if pct >= 80 then expandAlias("skill rodear") else expandAlias("skill corte_artero") end',
    [r"La defensa .* queda EXPUESTO \(\+(\d+) AC acumulado\)"],
)
make_trigger(pelea_trig_group, "Cooldown rodear", 'if en_combate and en_combate ~= 0 then expandAlias("skill rodear") end', [r"^El cooldown de rodear ha terminado\.$"])
make_trigger(pelea_trig_group, "Falta movimiento para corte artero", 'send("get melon moch")\nsend("comer melon")', [r"Te falta movimiento para arriesgar un corte artero ahora mismo"])
make_trigger(pelea_trig_group, "Raices y zarzas: totem oso", 'send("c \'totem animal oso\'")', [r"Haces brotar raices y zarzas que envuelven a (\w+)"])
make_trigger(pelea_trig_group, "Corte artero (auto)", 'expandAlias("skill corte_artero")', [r"^Tu corte artero"])
# "coce" es una habilidad RACIAL del centauro (no aparece en el comando
# "skills" del juego), no una skill con % de exito -- no tiene sentido
# pasarla por el wrapper "skill" (pensado para eso, con reintento en caso
# de fallo). Se manda directo, sin el eco de mas de "skill coce".
# Patron generico (no el nombre de un arma puntual): confirmado en juego
# que el texto cambia segun que herraduras tengas puestas ("...con
# herraduras Elficas.", "...con Unas Herraduras Claveteadas.", etc.) --
# con el nombre fijo, dejaba de disparar en cuanto cambiabas de arma.
make_trigger(pelea_trig_group, "Coces con herraduras (cualquier arma)", 'send("coce")', [r"recibe unas potentes Coces con .+\.$"])
make_trigger(
    pelea_trig_group, "Furia Salvaje: recuperado / sin totem",
    'expandAlias("skill furia")',
    [r"se recupera de los efectos de Furia Salvaje\.", r"No tienes ningun Totem Animal activo para usar Furia Salvaje\."],
)
make_trigger(pelea_trig_group, "Bosque bloqueado: abrir arbol", 'send("desblo arbol")\nsend("abrir arbol")\nsend("get todo arbol")', [r"escamoso te impide ver el bosque\.$"])
# NO se migra "te DESARMA enviando ... por los aires!" -- ya existe un sistema
# completo para esto en el paquete PetriaMUD_12.22.17 (Script "Desarmar":
# alias setarma/setsegun + DesarmePetria.recuperar), instalado aparte de
# este paquete "Petria". Tenerlo tambien aca duplicaria el re-equipar en
# cada desarme. Configurar con "setarma <palabra>" / "setsegun <palabra>".
make_trigger(pelea_trig_group, "Despejado de suciedad: espiar", 'send("espi")\ntempTimer(3, function() send("espi") end)', [r"se despeja de la suciedad de sus ojos\.$"])
make_trigger(pelea_trig_group, "Tu coz", 'send("coce")', [r"^Tu coz"])
make_trigger(pelea_trig_group, "Astucia gnoma se disipa (racial, no de clase)", 'expandAlias("skill astucia")', [r"Tu astucia gnoma se va disipan"])

# NOTA: no se migro el trigger CMUD con patron '{un|unos}(%1) * cercano, al  (%w).'
# (prioridad 23781, valor "%1 / k %1"). La sintaxis "(%1)" dentro del propio patron
# no es un wildcard estandar de CMUD y no pude traducirlo con confianza sin
# arriesgar un comportamiento incorrecto. Si sabes que hace, decime y lo migro.

# --- Subcarpeta ATAQUES ---
ataques_group = make_trigger_group(pelea_trig_group, "ATAQUES")
make_trigger(ataques_group, "Vulnerable al Rayo", 'rayo_ok = 1\nsend("c \'aliento tormentoso\'")', [r"vulnerable al Rayo\."])
make_trigger(ataques_group, "Vulnerable al Fuego", "fuego_ok = 1", [r"vulnerable al Fuego\."])
make_trigger(ataques_group, "Vulnerable al Acido", 'acido_ok = 1\nsend("c \\"golpe acido\\"")', [r"vulnerable al acido\."])

# --- Subcarpeta PK ---
# Mismo problema que WoF: patrones genericos como "esta aqui!$" matchean
# cualquier mob que aparezca en la sala, no solo un duelo PK real. En CMUD
# esta clase se activaba/desactivaba con #T+/#T- PK; aca se replica con un
# flag explicito "pkActivo" (default false) en vez de confiar solo en
# disableTriggerGroup.
pk_group = make_trigger_group(pelea_trig_group, "PK")

def make_pk_trigger(name, script, patterns):
    return make_trigger(pk_group, name, 'if not pkActivo then return end\n' + script, patterns)

make_pk_trigger(
    "Furia Salvaje falla: reintentar",
    'tempTimer(4, function()\n'
    '  if en_combate and en_combate ~= 0 and (not qcomm or qcomm <= 3) then send("skill furia") end\n'
    'end)',
    [r"Tu Furia Salvaje falla"],
)
make_pk_trigger(
    "Furia Salvaje activa: reintentar",
    'tempTimer(4, function()\n'
    '  if en_combate and en_combate ~= 0 and (not qcomm or qcomm <= 3) then send("skill furia") end\n'
    'end)',
    [r"!Furia Salvaje!"],
)
make_pk_trigger("Garrotazo de oso conecta", 'send("c \'totem animal buho\'")', [r"Tu garrotazo de oso conecta la boca de tu rival! Lo golpetea\."])
make_pk_trigger("PK: objetivo esta aqui", 'if rasOBJ and rasOBJ ~= "" then expandAlias("engancha " .. rasOBJ) end', [r"^(.*) esta aqui!$"])
make_pk_trigger("PK: objetivo huyo", 'if rasOBJ and rasOBJ ~= "" then send("ras " .. rasOBJ) end', [r"ha huido!$"])
make_pk_trigger("Poder del oso ancestral (PK)", 'send("espinillazo")\nsend("skill furia")', [r"^Ahora, caminas con el poder y la ferocidad del oso ancestral\.$"])

# --- Subcarpeta WoF ---
# WoF (Guerra de Facciones) comparte patrones de texto con el combate PvE
# normal (ej. "han sido cegados por la suciedad!" tambien matchea en Pelea).
# Confirmado en juego: aunque "k" llama a disableTriggerGroup("WoF"), un
# trigger de WoF disparo igual junto al de Pelea (huir x3 en vez de solo
# zancadilla), haciendo perder un combate que se estaba ganando. En vez de
# confiar solo en disableTriggerGroup, cada trigger de WoF chequea el flag
# explicito "wofActivo" (default false) antes de hacer nada.
wof_group = make_trigger_group(pelea_trig_group, "WoF")

def make_wof_trigger(name, script, patterns):
    return make_trigger(wof_group, name, 'if not wofActivo then return end\n' + script, patterns)

make_wof_trigger(
    "Amigo WoF se va por una salida",
    'local nombre, direccion = matches[2], matches[3]\n'
    'if WoFriends[nombre] then\n'
    '  send(direccion)\n'
    '  send("k " .. nombre)\n'
    'end',
    [r"(\w+) se va por el (\w+)\.$"],
)
make_wof_trigger(
    "Huida cobarde: curar y recall",
    'pcall(disableTriggerGroup, "PK")\n'
    'send("ocu")\nsend("traga sanar")\nsend("c sanar")\nsend("c sanar")\nsend("za")\nsend("traga santu")\n'
    'if rasOBJ and rasOBJ ~= "" then send("ras " .. rasOBJ) end',
    [r"^¡?Logras HUIR!  \.\.\.Cobardemente\.\.\."],
)
make_wof_trigger("Poder del oso ancestral (WoF)", 'send("espinillazo")\nsend("huir")\nsend("huir")', [r"^Ahora, caminas con el poder y la ferocidad del oso ancestral\.$"])
make_wof_trigger("Cegados por suciedad: huir", 'send("huir")\nsend("huir")\nsend("huir")', [r"han sido cegados por la suciedad!$"])
make_wof_trigger(
    "Amigo WoF justo aqui",
    'local nombre = matches[2]\n'
    'if WoFriends[nombre] then expandAlias("k " .. nombre) end',
    [r"^(\w+), justo aqui\.$"],
)
make_wof_trigger(
    "Amigo WoF ha huido",
    'local nombre = matches[2]\n'
    'if WoFriends[nombre] then send("ras " .. nombre) end',
    [r"^(\w+) ha huido!$"],
)
make_wof_trigger("WoF: objetivo esta aqui", 'if rasOBJ and rasOBJ ~= "" then expandAlias("engancha " .. rasOBJ) end', [r"^(.*) esta aqui!$"])
make_wof_trigger(
    "Esquina norte del campo de batalla",
    'send("e")\nsend("e")\nsend("scan")\n'
    'if rasOBJ and rasOBJ ~= "" then send("k " .. rasOBJ); send("k " .. rasOBJ); send("k " .. rasOBJ) end',
    [r"ESQUINA NORTE DEL CAMPO DE BATALLA .*\(No Rastrear\)"],
)
make_wof_trigger(
    "Esquina sur del campo de batalla",
    'send("w")\nsend("w")\nsend("scan")\n'
    'if rasOBJ and rasOBJ ~= "" then send("k " .. rasOBJ); send("k " .. rasOBJ); send("k " .. rasOBJ) end',
    [r"ESQUINA SUR DEL CAMPO DE BATALLA .*\(No Rastrear\)"],
)

# --- Subcarpeta acoso ---
# Consolidado en UN solo trigger (en vez de 13 separados) porque el original de
# CMUD usa "@acosado" interpolado DENTRO del patron -- eso es dinamico en CMUD
# pero un regex de Mudlet es estatico. La forma correcta y simple de replicarlo:
# un trigger que matchea cualquier linea, filtra por Lua si contiene el nombre
# actual de "acosado", y despues distingue el caso exacto con if/elseif.
acoso_group = make_trigger_group(pelea_trig_group, "acoso")
make_trigger(
    acoso_group, "Acoso: despachador",
    '''if not acosado or acosado == "" then return end
local line = matches[1]

-- Estas 3 no mencionan el nombre del acosado, se revisan antes del filtro:
if line:find("Cogelo!", 1, true)
    or line:find("Logras HUIR!", 1, true)
    or line:find("Uy Uy, que te pillan", 1, true) then
  pcall(disableTriggerGroup, "acoso")
  cecho(string.format("<yellow>Mejor ya no acosar a %s\\n", acosado))
  return
end

if not line:find(acosado, 1, true) then return end

local direccion = line:match(acosado .. ".* se va por el (%a+)")
local direccionCercano = line:match(acosado .. ",? cercano,? al%s+(%a+)%.")

if line:find(acosado .. " aparece en la habitacion", 1, true) then
  send("ki " .. acosado)
elseif line:find(acosado .. " ha llegado.", 1, true) then
  send("k " .. acosado)
elseif direccion then
  send(direccion)
  send("k " .. acosado)
elseif line:find(acosado .. ", justo aqui.", 1, true) then
  send("k " .. acosado)
elseif direccionCercano then
  send(direccionCercano)
  send("k " .. acosado)
elseif line:find(acosado .. " abre el/la puerta.", 1, true) then
  send("k " .. acosado)
elseif line:find("Haces zap a " .. acosado .. " con una rama de Ent.", 1, true) then
  send("c deslu " .. acosado)
elseif line:find(acosado .. " es descubierto!!", 1, true) then
  send("k " .. acosado)
elseif line:find("solicita un quest a el Dios Probador", 1, true) then
  send("ki " .. acosado)
end''',
    [r"(.*)"],
)

ET.SubElement(root, "TimerPackage")

# ---------- AliasPackage ----------
alias_pkg = ET.SubElement(root, "AliasPackage")

def make_alias_group(parent, name):
    g = ET.SubElement(parent, "AliasGroup", {"isActive": "yes", "isFolder": "yes"})
    ET.SubElement(g, "name").text = name
    ET.SubElement(g, "script").text = ""
    ET.SubElement(g, "command").text = ""
    ET.SubElement(g, "packageName").text = ""
    ET.SubElement(g, "regex").text = ""
    return g

def make_alias(parent, name, regex, script):
    a = ET.SubElement(parent, "Alias", {"isActive": "yes", "isFolder": "no"})
    ET.SubElement(a, "name").text = name
    ET.SubElement(a, "script").text = script
    ET.SubElement(a, "command").text = ""
    ET.SubElement(a, "packageName").text = ""
    ET.SubElement(a, "regex").text = regex
    return a

petria_alias_group = make_alias_group(alias_pkg, "Petria-Rhuna")
clases_alias_group = make_alias_group(petria_alias_group, "Clases")
pelea_alias_group = make_alias_group(petria_alias_group, "Pelea")

make_alias(
    clases_alias_group, "k", r"^k(?: (.+))?$",
    'local obj = matches[2] or ""\n'
    'rasOBJ = obj\n'
    'pcall(disableTriggerGroup, "WoF")\n'
    'pcall(enableTriggerGroup, "Pelea")\n\n'
    'if obj ~= "" and clase and Clases.clasesConEmpalar[clase] and not (en_combate and en_combate ~= 0) then\n'
    '  Clases.intentarEmpalar(obj)\n'
    'end\n\n'
    'Clases.despacharAtaque(obj)'
)

# "kk": igual que "k" pero SIN el intento de empalar -- para cuando ya
# estas en combate (ej. te atacaron primero) y solo queres que dispare los
# ataques de la ficha de la clase, sin perder turnos cambiando a lanza.
make_alias(
    clases_alias_group, "kk", r"^kk(?: (.+))?$",
    'local obj = matches[2] or ""\n'
    'rasOBJ = obj\n'
    'pcall(disableTriggerGroup, "WoF")\n'
    'pcall(enableTriggerGroup, "Pelea")\n\n'
    'send("c \'curar deslumbrar\'")\n\n'
    '-- Tip de PK: "vision" (gatovision + vision verdadera) primero, porque\n'
    '-- es lo que permite que la cancelacion despues realmente quite\n'
    '-- santuario/acelerar del rival. Solteados si ya estan activos.\n'
    'if not Clases.tieneActivo("gatovision") then\n'
    '  send("c gatovision")\n'
    'end\n'
    'if not Clases.tieneActivo("vision verdadera") then\n'
    '  send("conjurar \'vision verdadera\'")\n'
    'end\n\n'
    '-- Si el atacante esta identificado (no "Someone", que es lo que manda\n'
    '-- el server cuando no lo podes ver/detectar -- ver alerta de PK en\n'
    '-- Pelea), cancelamos lo que este canalizando via el alias "can" ya\n'
    '-- existente (reintento incluido).\n'
    'if obj ~= "" and obj:lower() ~= "someone" then\n'
    '  expandAlias("can " .. obj)\n'
    'end\n\n'
    'Clases.despacharAtaque(obj)'
)

make_alias(
    clases_alias_group, "engancha", r"^engancha (.+)$",
    'local obj = matches[2]\n'
    'if clase and Clases[clase] and Clases[clase].engancha then\n'
    '  Clases[clase].engancha(obj)\n'
    'else\n'
    '  cecho(string.format("<red>?? Clase desconocida: %s\\n", tostring(clase)))\n'
    '  send("mata " .. obj)\n'
    'end'
)

make_alias(
    clases_alias_group, "panico", r"^panico$",
    'pcall(disableTriggerGroup, "PK")\n'
    'pcall(disableTriggerGroup, "WoF")\n'
    'pcall(disableTriggerGroup, "acoso")\n'
    'pcall(disableTriggerGroup, "Pelea")\n'
    'wofActivo = false\n'
    'pkActivo = false\n'
    'en_combate = 0\n'
    'send("huir")\n'
    'send("huir")\n'
    'send("recall")'
)

# Per-class recall aliases (thin wrappers over Clases.X.recall)
# Claves en minuscula: deben matchear el valor de "clase" que llega por GMCP
# (gmcp.Char.Base.class:lower()), no el nombre de la carpeta/script.
recall_aliases = {
    "cguerrero": "guerrero",
    "cmagos": "mago",
    "cladron": "ladron",
    "cranger": "ranger",
    "cdruida": "druida",
    "casesino": "asesino",
}
for alias_name, clase_name in recall_aliases.items():
    make_alias(
        clases_alias_group, alias_name, f"^{alias_name}$",
        f'send("recall")\n'
        f'if Clases.{clase_name} and Clases.{clase_name}.recall then\n'
        f'  Clases.{clase_name}.recall()\n'
        f'end'
    )

# "coteren" faltaba como recall dedicado (existia en CMUD pero no estaba
# asociado a ninguna clase reconocida antes) -- es el recall de Seguidores.
make_alias(
    clases_alias_group, "coteren", r"^coteren$",
    'send("recall")\n'
    'if Clases.seguidores and Clases.seguidores.recall then\n'
    '  Clases.seguidores.recall()\n'
    'end'
)

make_alias(
    clases_alias_group, "dope", r"^dope(?: (.+))?$",
    '-- Antes en CMUD "dope" (generico) llamaba a una funcion inexistente\n'
    '-- (dope_continuar) y quedaba a medias. Ahora despacha directo a los\n'
    '-- hechizos de la clase conectada (gmcp.Char.Base.class).\n'
    'local obj = matches[2] or ""\n'
    'if clase and Clases[clase] and Clases[clase].dope then\n'
    '  Clases[clase].dope(obj)\n'
    'else\n'
    '  cecho(string.format("<red>No hay hechizos de dope definidos para la clase \'%s\'.\\n", tostring(clase)))\n'
    'end'
)

make_alias(
    clases_alias_group, "addspell", r"^addspell (.+)$",
    'local hechizo = matches[2]:lower()\n'
    'if not clase or clase == "" then\n'
    '  cecho("<red>Todavia no se detecto tu clase (esperando GMCP).\\n")\n'
    '  return\n'
    'end\n'
    'Clases.dopes[clase] = Clases.dopes[clase] or {}\n'
    'for _, h in ipairs(Clases.dopes[clase]) do\n'
    '  if h:lower() == hechizo then\n'
    '    cecho(string.format("<yellow>\'%s\' ya estaba en la lista de dope de %s.\\n", hechizo, clase))\n'
    '    return\n'
    '  end\n'
    'end\n'
    'table.insert(Clases.dopes[clase], hechizo)\n'
    'Clases.guardarDopes()\n'
    'cecho(string.format("<green>Agregado \'%s\' al dope de %s (guardado).\\n", hechizo, clase))'
)

make_alias(
    clases_alias_group, "removespell", r"^removespell (.+)$",
    'local hechizo = matches[2]:lower()\n'
    'if not clase or clase == "" then\n'
    '  cecho("<red>Todavia no se detecto tu clase (esperando GMCP).\\n")\n'
    '  return\n'
    'end\n'
    'local lista = Clases.dopes[clase]\n'
    'if not lista then\n'
    '  cecho(string.format("<yellow>No hay lista de dope para %s.\\n", clase))\n'
    '  return\n'
    'end\n'
    'for i, h in ipairs(lista) do\n'
    '  if h:lower() == hechizo then\n'
    '    table.remove(lista, i)\n'
    '    Clases.guardarDopes()\n'
    '    cecho(string.format("<green>Sacado \'%s\' del dope de %s (guardado).\\n", hechizo, clase))\n'
    '    return\n'
    '  end\n'
    'end\n'
    'cecho(string.format("<yellow>\'%s\' no estaba en la lista de dope de %s.\\n", hechizo, clase))'
)

make_alias(
    pelea_alias_group, "skill", r"^skill (.+)$",
    '-- Guarda el comando completo para poder reintentarlo (ver triggers\n'
    '-- "Hechizo fallado" / "Reintentar skill tras fallo") y lo ejecuta.\n'
    'ultima_skill = "skill " .. matches[2]\n'
    'send(matches[2])'
)

make_alias(
    pelea_alias_group, "wof", r"^wof (on|off)$",
    'wofActivo = (matches[2] == "on")\n'
    'cecho(string.format("<cyan>[Pelea] WoF %s.\\n", wofActivo and "activado" or "desactivado"))'
)
make_alias(
    pelea_alias_group, "pk", r"^pk (on|off)$",
    'pkActivo = (matches[2] == "on")\n'
    'cecho(string.format("<cyan>[Pelea] PK %s.\\n", pkActivo and "activado" or "desactivado"))'
)

ataques_alias_group = make_alias_group(pelea_alias_group, "ATAQUES")

# cast00/01/02 usan los flags rayo_ok/fuego_ok/acido_ok, seteados por los
# triggers de texto "vulnerable al Rayo/Fuego/acido." (mas abajo). Esto
# rastrea si el ENEMIGO quedo vulnerable tras castearle la debilidad
# correspondiente. gmcp.Char.Affects.vulnerable NO sirve para esto: ese
# campo es la vulnerabilidad del PERSONAJE CONECTADO (cuelga de gmcp.Char,
# no de gmcp.Char.Enemies), asi que se descarto esa idea.
make_alias(
    ataques_alias_group, "cast00", r"^cast00$",
    'if acido_ok and acido_ok ~= 0 then\n'
    '  send("c \'" .. (ataque00 or "") .. "\'")\n'
    'else\n'
    '  send("c \'debilidad acida\'")\n'
    '  send("c \'" .. (ataque00 or "") .. "\'")\n'
    'end'
)
make_alias(
    ataques_alias_group, "cast01", r"^cast01$",
    'if rayo_ok and rayo_ok ~= 0 then\n'
    '  send("c \'" .. (ataque01 or "") .. "\'")\n'
    'else\n'
    '  send("c \'debilidad rayo\'")\n'
    '  send("c \'" .. (ataque01 or "") .. "\'")\n'
    'end'
)
make_alias(
    ataques_alias_group, "cast02", r"^cast02$",
    'if fuego_ok and fuego_ok ~= 0 then\n'
    '  send("c \'" .. (ataque02 or "") .. "\'")\n'
    'else\n'
    '  send("c \'debilidad fuego\'")\n'
    '  send("c \'" .. (ataque02 or "") .. "\'")\n'
    'end'
)

# ---------- Alias/Petria/Alias (resto de 18-Alias de CMUD) ----------
# dd/ddo/ddq quedan afuera a proposito: son parte del motor DD-Engine
# (dd_mob, dd_callback, quest_state, dd_vnums...) y se migran junto con esa
# carpeta, no aca.
alias_group = make_alias_group(petria_alias_group, "Alias")

# OJO paths: CMUD usa notacion compacta con "." (ej. ".4sw") para caminar
# rapido. En este Mudlet/server, un mensaje que EMPIEZA con "." se interpreta
# como GRITAR, no como camino (confirmado en juego: ".feo ." -> "Gritas 'feo
# .'"). Por eso todos los paths se expandieron a pasos individuales n/s/e/w
# (confirmados como validos) en vez de mandar la notacion compacta con punto.
# Diagonales (ej. "sw" en ".4sw") se descompusieron en 2 pasos cardinales en
# vez de un solo comando diagonal, para no arriesgar la letra exacta (evitar
# apostar entre "sw" ingles vs "so" español para suroeste, etc.).
make_alias(alias_group, "donas", r"^donas$", 'send("recall")\nClases.sendSeq("s", "w", "s", "w", "s", "w", "s", "w")')
make_alias(alias_group, "mm", r"^mm (.+)$", 'send("c \'misil magico\' " .. matches[2])')
make_alias(alias_group, "pan", r"^pan$", 'Clases.sendSeq("s", "s", "w", "n")')
make_alias(alias_group, "bc", r"^bc$", 'Clases.sendSeq("s", "e", "s", "e", "s", "e", "s", "e", "s", "e")')

make_alias(
    alias_group, "pocionesfull", r"^pocionesfull$",
    '-- Las lineas "comprar 2/2" y "comprar 3/3" del original estaban\n'
    '-- comentadas ("//") en CMUD -- tambien quedan sin ejecutar aca.\n'
    '-- "banco" ya deposita/retira por su cuenta (ingresar todo/rei 4000) --\n'
    '-- no se duplica esa logica aca, solo se espera la confirmacion del\n'
    '-- retiro antes de seguir con la compra.\n'
    'send("banco")\n'
    'Petria.esperarTexto("El Banquero de Midgaard dice \'despues de retirar: 4000 monedas\\\\.\'", function()\n'
    '  send("recall")\n'
    '  send("n")\n'
    '  Clases.sendSeq("s", "s", "s", "s", "e", "e", "e", "n")\n'
    '  tempTimer(0.5, function()\n'
    '    send("comprar 30*4")\n'
    '    tempTimer(0.5, function()\n'
    '      send("abrir moch")\n'
    '      tempTimer(0.5, function()\n'
    '        send("pon todo moch")\n'
    '      end)\n'
    '    end)\n'
    '  end)\n'
    'end, 15)'
)

make_alias(alias_group, "saciar", r"^saciar$", 'Clases.sendSeq("n", "n", "n", "n", "n")\nsend("beber")')
make_alias(alias_group, "limo", r"^limo$", 'send("recall")\nClases.sendSeq("n", "n", "n", "n", "n")\nfor i = 1, 6 do send("bebe") end')
make_alias(alias_group, "arena", r"^arena$", 'send("recall")\nClases.sendSeq("n", "n", "n", "n", "n", "w", "w", "n")\nsend("dar 10 oro cobrador")')
make_alias(alias_group, "banco", r"^banco$", 'send("recall")\nsend("n")\nsend("ir Banco")\nsend("ingresar todo")\nsend("rei 4000")')

make_alias(
    alias_group, "pocsantu", r"^pocsantu$",
    'send("recall")\n'
    'send("n")\n'
    'Petria.esperarTexto("El Altar del Templo", function()\n'
    '  send("ir ofcol")\n'
    '  Clases.sendSeq("n", "e", "n", "e")\n'
    '  tempTimer(0.5, function()\n'
    '    for i = 1, 5 do send("comprar 1") end\n'
    '  end)\n'
    'end, 15)'
)

make_alias(alias_group, "reca", r"^reca$", 'send("recall")\nsend("norte")\nsend("lista")')
make_alias(alias_group, "ata", r"^ata$", 'send("c sp " .. (rasOBJ or ""))')
make_alias(alias_group, "lobj", r"^lobj (.+)$", 'send("c \'localizar objeto\' " .. matches[2])')

make_alias(
    alias_group, "toma", r"^toma (.+)$",
    'eqdonas = matches[2]\n'
    'retryEQ = 0\n'
    'pcall(enableTriggerGroup, "11-EQ")\n'
    'send("get " .. eqdonas)\n'
    'send("tradi " .. matches[2])'
)

make_alias(
    alias_group, "fdope", r"^fdope$",
    'send("traga trans")\nsend("traga gris")\nsend("traga azul")\nsend("traga santuario")\n'
    'expandAlias("dope")\nexpandAlias("dope")\nexpandAlias("dope")'
)
make_alias(alias_group, "ihs", r"^ihs$", 'send("traga gris")\nsend("traga trans")\nsend("traga santu")')
make_alias(alias_group, "portal", r"^portal (.+)$", 'send("c compuerta " .. matches[2])')

make_alias(
    alias_group, "can", r"^can (.+)$",
    '-- Version original (#LOOP 1,2 de CMUD, 2 intentos): confirmado en\n'
    '-- juego que "cancelacion" falla seguido ("Hechizo fallado.", un %\n'
    '-- de exito del propio hechizo, no relacionado a si hay algo para\n'
    '-- cancelar) -- 2 intentos se quedaban cortos muy seguido, necesito\n'
    '-- 6-7 reintentos reales para que conecte. Subido a 6. Tambien corta\n'
    '-- temprano si el server dice "Nada que cancelar." (no tiene sentido\n'
    '-- seguir intentando si el objetivo no tiene nada activo).\n'
    'local tarjet = matches[2]\n'
    'local intentos = 0\n'
    'local intentosMax = 6\n'
    'local terminado = false\n\n'
    'local function intentar()\n'
    '  intentos = intentos + 1\n'
    '  send("c \'cancelacion\' " .. tarjet)\n'
    '  local idExito, idNada\n'
    '  local function limpiar()\n'
    '    if exists(idExito, "trigger") == 1 then killTrigger(idExito) end\n'
    '    if exists(idNada, "trigger") == 1 then killTrigger(idNada) end\n'
    '  end\n'
    '  idExito = tempRegexTrigger("se desvanece\\\\.|Ok\\\\.", function()\n'
    '    if terminado then return end\n'
    '    terminado = true\n'
    '    limpiar()\n'
    '    cecho(string.format("<green>Cancelacion exitosa en %d intento(s).\\n", intentos))\n'
    '  end)\n'
    '  idNada = tempRegexTrigger("Nada que cancelar\\\\.", function()\n'
    '    if terminado then return end\n'
    '    terminado = true\n'
    '    limpiar()\n'
    '    cecho("<gray>Nada que cancelar en el objetivo.\\n")\n'
    '  end)\n'
    '  tempTimer(0.7, function()\n'
    '    if not terminado then\n'
    '      limpiar()\n'
    '      if intentos < intentosMax then\n'
    '        intentar()\n'
    '      else\n'
    '        cecho(string.format("<red>Cancelacion fallida tras %d intentos.\\n", intentosMax))\n'
    '      end\n'
    '    end\n'
    '  end)\n'
    'end\n\n'
    'intentar()'
)

make_alias(alias_group, "pb", r"^pb$", "send(\"c 'proteccion divina'\")")
make_alias(alias_group, "pm", r"^pm$", "send(\"c 'proteccion infernal'\")")
make_alias(alias_group, "rp", r"^rp (.+)$", "send(\"conjurar 'rayo poderoso' \" .. matches[2])")
make_alias(alias_group, "fuen", r"^fuen$", 'send("c fuente")')
make_alias(alias_group, "alqui", r"^alqui (.+)$", "send(\"c 'mejora alquimica' \" .. matches[2])")

make_alias(
    alias_group, "eds", r"^eds$",
    'send("c tras")\nsend("disimular")\nsend("c invis")\nsend("esconder")\nsend("ocultar")\nsend("c volar")\nsend("c tras")'
)
make_alias(alias_group, "rol", r"^rol (.+)$", 'send("emote [ROL] " .. matches[2])')

make_alias(
    alias_group, "cambio", r"^cambio$",
    '-- "//ras otho" estaba comentado en el original, queda sin ejecutar\n'
    'send("recall")\n'
    'Clases.sendSeq("n", "n", "n", "n", "n", "w", "w", "s")\n'
    'send("sc")\n'
    'tempTimer(3, function() send("dar " .. tostring(plata) .. " plata otho") end)'
)

make_alias(
    alias_group, "pociones", r"^pociones$",
    '-- "banco" ya deposita/retira por su cuenta (ingresar todo/rei 4000) --\n'
    '-- no se duplica esa logica aca.\n'
    'send("banco")\n'
    'send("recall")\nsend("n")\nClases.sendSeq("s", "s", "s", "s", "e", "e", "e", "n")\n'
    'tempTimer(0.5, function() send("lista") end)'
)

make_alias(alias_group, "cq", r"^cq$", 'send("quien concilio")')

make_alias(
    alias_group, "updatepkg", r"^updatepkg(?:\s+(-v|version))?$",
    '-- "updatepkg -v" (o "updatepkg version"): solo muestra el build\n'
    '-- instalado (Petria.version, timestamp unix de build_petria_package.py)\n'
    '-- sin reinstalar nada -- para confirmar de un vistazo si esta\n'
    '-- sincronizado con el ultimo push, en vez de tener que comparar el\n'
    '-- comportamiento de los alias a mano.\n'
    'if matches[2] and matches[2] ~= "" then\n'
    '  cecho(string.format("<cyan>[Petria-Rhuna] Build instalado: %s\\n", tostring(Petria.version)))\n'
    '  return\n'
    'end\n\n'
    '-- uninstallPackage + installPackage encadenados en una sola linea daban\n'
    '-- "package X is already installed" por timing (confirmado antes, por\n'
    '-- eso veniamos pidiendo hacerlo en dos comandos separados). El\n'
    '-- tempTimer da tiempo a que el uninstall termine antes de reinstalar.\n'
    '-- Nombre "Petria-Rhuna" (no "Petria" a secas) a proposito: el server\n'
    '-- tiene un comando "instalarmudlet" que instala/actualiza su propio\n'
    '-- paquete GUI oficial, y ese instalador sobreescribe cualquier package\n'
    '-- Mudlet que tenga EL MISMO NOMBRE -- si el nuestro se llamara igual\n'
    '-- que el oficial (o algo generico como "Petria"), correr\n'
    '-- "instalarmudlet" en el juego podria borrar todo esto.\n'
    '-- Instala desde GitHub (via jsdelivr), no un archivo local: asi\n'
    '-- funciona igual en cualquier PC, no solo en la que genero el archivo.\n'
    '-- Se usa jsdelivr.net en vez de raw.githubusercontent.com porque esta\n'
    '-- ultima quedo bloqueada en la red corporativa de la Mac (confirmado\n'
    '-- con curl: "Connection reset by peer" tanto directo como via el\n'
    '-- redirect de github.com/.../raw/...). jsdelivr es un CDN publico\n'
    '-- que espeja repos de GitHub y no tuvo ese bloqueo.\n'
    '-- "?v=<timestamp>" al final: confirmado en juego que Mudlet cachea la\n'
    '-- respuesta HTTP del lado del cliente ademas del CDN -- purgar\n'
    '-- jsdelivr no alcanzaba, updatepkg seguia trayendo la version vieja.\n'
    '-- Cambia en cada build de este script, asi la url es "nueva" siempre.\n'
    '-- Confirmado en juego, dos veces seguidas: installPackage() desde una\n'
    '-- URL puede fallar en silencio (sin "[INFO] Downloading"/"[OK]\n'
    '-- installed") si se llama muy pronto despues de uninstallPackage --\n'
    '-- 0.5s de por medio (el delay original) no alcanzaba siempre. Subido\n'
    '-- a 2s antes del primer intento, mas UN reintento automatico con otros\n'
    '-- 3s de por medio si getPackages() confirma que sigue sin quedar\n'
    '-- instalado (antes cecho-eabamos "Reinstalado." sin chequear nada, y\n'
    '-- el usuario se quedaba con el paquete DESINSTALADO creyendo que\n'
    '-- habia andado bien, rompiendo todos los alias).\n'
    'cecho("<yellow>[Petria-Rhuna] Reinstalando...\\n")\n'
    'uninstallPackage("Petria-Rhuna")\n\n'
    'local function PetriaRhunaEstaInstalado()\n'
    '  for _, nombre in ipairs(getPackages()) do\n'
    '    if nombre == "Petria-Rhuna" then return true end\n'
    '  end\n'
    '  return false\n'
    'end\n\n'
    'local function PetriaRhunaVerificar(intento)\n'
    '  if PetriaRhunaEstaInstalado() then\n'
    '    cecho("<green>[Petria-Rhuna] Reinstalado.\\n")\n'
    '  elseif intento < 2 then\n'
    '    cecho(string.format("<yellow>[Petria-Rhuna] Intento %d fallo, reintentando...\\n", intento))\n'
    f'    installPackage("{JSDELIVR_URL}")\n'
    '    tempTimer(3, function() PetriaRhunaVerificar(intento + 1) end)\n'
    '  else\n'
    f'    cecho("<red>[Petria-Rhuna] FALLO el reinstall tras 2 intentos. Instalalo manual: lua installPackage(\\"{JSDELIVR_URL}\\")\\n")\n'
    '  end\n'
    'end\n\n'
    'tempTimer(2, function()\n'
    f'  installPackage("{JSDELIVR_URL}")\n'
    '  tempTimer(3, function() PetriaRhunaVerificar(1) end)\n'
    'end)'
)
make_alias(alias_group, "q", r"^q (.+)$", 'send("get " .. matches[2] .. " moch")\nsend("tra " .. matches[2])')
make_alias(alias_group, "gp", r"^gp$", 'send("golpetazo")')
make_alias(alias_group, "toso", r"^toso$", "send(\"c 'totem animal oso'\")")
make_alias(alias_group, "ttortu", r"^ttortu$", "send(\"c 'totem animal tortuga'\")")
make_alias(alias_group, "canimal", r"^canimal (.+)$", "send(\"c 'control animal' \" .. matches[2])")
make_alias(alias_group, "des", r"^des$", 'send("c deslu " .. (rasOBJ or ""))')
make_alias(alias_group, "mal", r"^mal$", 'send("c maldecir " .. (rasOBJ or ""))')
make_alias(alias_group, "rai", r"^rai$", 'send("c raices " .. (rasOBJ or ""))')
make_alias(alias_group, "tbuho", r"^tbuho$", "send(\"c 'totem animal buho'\")")
make_alias(alias_group, "bazar", r"^bazar$", 'send(\'c clari "nomada"\')')
make_alias(alias_group, "cs", r"^cs$", 'send("decir curata spells")')
make_alias(alias_group, "co", r"^co (.+)$", 'local t = matches[2]\nsend("contragolpe " .. t)\nsend("espini " .. t)\nsend("zanca " .. t)')
make_alias(alias_group, "cc", r"^cc (.+)$", "local t = matches[2]\nsend(\"c 'curar deslumbrar' \" .. t)\nsend(\"c 'curar critico' \" .. t)")
make_alias(alias_group, "asa", r"^asa (.+)$", 'local t = matches[2]\nexpandAlias("can " .. t)\nsend("c rai " .. t)\nsend("hui n")')
make_alias(alias_group, "fabada", r"^fabada$", 'send("creg")\nsend("ras Idhrall")')
make_alias(alias_group, "za", r"^za$", 'send("get puntero moch")\nsend("sos puntero")\nsend("zap self")')

make_alias(
    alias_group, "ene", r"^ene (add|del) (.+)$",
    'local accion, nombre = matches[2], matches[3]\n'
    'if accion == "add" then\n'
    '  if not WoFriends[nombre] then\n'
    '    WoFriends[nombre] = true\n'
    '    cecho(string.format("<green>---> %s agregado a lista de ENEMIGOS.\\n", nombre))\n'
    '  else\n'
    '    cecho("<yellow>---> ya estaba en la lista.\\n")\n'
    '  end\n'
    'else\n'
    '  if WoFriends[nombre] then\n'
    '    WoFriends[nombre] = nil\n'
    '    cecho(string.format("<green>---> %s eliminado de ENEMIGOS.\\n", nombre))\n'
    '  else\n'
    '    cecho("<yellow>---> no estaba en la lista.\\n")\n'
    '  end\n'
    'end'
)

make_alias(alias_group, "aa", r"^aa (.+)$", 'send("desbloquear " .. matches[2])\nsend("abrir " .. matches[2])')

make_alias(
    alias_group, "pescaron", r"^pescaron$",
    'send("get caña moch")\nsend("vest caña")\nsend("get red moch")\nsend("bla red")\n'
    'send("pon libro moch")\nsend("gua escudo")\nsend("pon escudo moch")\nsend("usar caña")'
)

make_alias(
    alias_group, "rayo", r"^rayo (.+)$",
    'local t = matches[2]\n'
    'send("c summon cochero")\n'
    'Petria.esperarTexto("El cochero aparece de repente\\\\.", function()\n'
    '  send("c rayo " .. t)\n'
    'end, 15)'
)

make_alias(alias_group, "encantar", r"^encantar (.+)$", "send(\"c 'encantar gente' \" .. matches[2])")

make_alias(
    alias_group, "defender", r"^defender$",
    'send("ir 11864")\n'
    'send("can " .. (enemigo or ""))\n'
    'send("c debilitar " .. (enemigo or ""))\n'
    'send("huir e"); send("huir e"); send("huir e")\n'
    'send("ir 11866")'
)

ET.SubElement(root, "ActionPackage")

# ---------- ScriptPackage ----------
script_pkg = ET.SubElement(root, "ScriptPackage")

def make_script_group(parent, name):
    g = ET.SubElement(parent, "ScriptGroup", {"isActive": "yes", "isFolder": "yes"})
    ET.SubElement(g, "name").text = name
    ET.SubElement(g, "packageName").text = ""
    ET.SubElement(g, "script").text = ""
    ET.SubElement(g, "eventHandlerList")
    return g

def make_script(parent, name, script):
    s = ET.SubElement(parent, "Script", {"isActive": "yes", "isFolder": "no"})
    ET.SubElement(s, "name").text = name
    ET.SubElement(s, "packageName").text = ""
    ET.SubElement(s, "script").text = script
    ET.SubElement(s, "eventHandlerList")
    return s

petria_script_group = make_script_group(script_pkg, "Petria-Rhuna")

petria_core_script = f'''-- ================================================================
-- PETRIA CORE - utilidades compartidas
-- ================================================================
-- Equivalente a #WAITFOR y #WAIT de CMUD, que no existen tal cual en
-- Mudlet. Petria.esperarTexto crea un trigger temporal que se autoelimina
-- despues de disparar una vez (o al vencer el timeout).
-- ================================================================

Petria = Petria or {{}}

-- Timestamp unix de cuando se corrio build_petria_package.py para este
-- build. Sirve para "updatepkg -v": confirmar de un vistazo si lo
-- instalado esta sincronizado con el ultimo push, sin tener que comparar
-- el contenido de los alias a mano cada vez que algo no anda.
Petria.version = {JSDELIVR_CACHE_BUSTER}

function Petria.esperarTexto(patron, callback, timeoutSeg)
  local id
  id = tempRegexTrigger(patron, function()
    killTrigger(id)
    callback()
  end)
  if timeoutSeg then
    tempTimer(timeoutSeg, function()
      if exists(id, "trigger") == 1 then
        killTrigger(id)
      end
    end)
  end
  return id
end

-- Variables sueltas usadas por varios alias de 18-Alias (CMUD)
eqdonas = eqdonas or ""
retryEQ = retryEQ or 0
plata = plata or 0
enemigo = enemigo or ""
'''
make_script(petria_script_group, "Petria_Core", petria_core_script)

clases_group = make_script_group(petria_script_group, "Clases")

core_script = '''-- ================================================================
-- CLASES DE PERSONAJE - PetriaMUD
-- ================================================================
-- Cada subcarpeta de "Clases" define Clases.<Nombre> con sus
-- funciones especiales (ataque, engancha, recall). El alias "k"
-- y "engancha" solo despachan a la clase activa (variable global
-- "clase").
--
-- La clase se lee de GMCP (gmcp.Char.Base.class), igual que ya usa
-- el panel "Informacion del Personaje" del paquete PetriaMUD_12.22.17
-- (funcion obtenerDatosPersonaje / datos.clase) -- no se vuelve a
-- parsear texto de "sc" ni de ningun otro comando.
--
-- Migrado desde CMUD (alias k / engancha / panico / c<clase>).
-- ================================================================

-- Nota: sin guard de "cargado una sola vez" a proposito. Este paquete se
-- reinstala seguido durante el desarrollo (uninstallPackage + installPackage)
-- y un guard global habria bloqueado el re-registro del handler GMCP y el
-- seteo inicial de "clase" en cada reinstalacion.

Clases = Clases or {}
clase = clase or nil

function Clases.sendSeq(...)
  for _, cmd in ipairs({...}) do
    send(cmd)
  end
end

-- "astu" (astucia gnoma) es una habilidad racial, solo para gnomos. El
-- dopem/dopeo original de CMUD la mandaba sin condicion para cualquier
-- raza (confirmado en juego: "Te esfuerzas, pero no logras activar
-- astucia gnoma ... solo para gnomos..." con un personaje centauro).
function Clases.intentarAstucia()
  if gmcp and gmcp.Char and gmcp.Char.Base and gmcp.Char.Base.race
     and gmcp.Char.Base.race:lower() == "gnomo" then
    send("astu")
  end
end

-- true si el nombre del hechizo aparece en gmcp.Char.Affects.BuffYDebuff
-- (los hechizos que el personaje tiene activos ahora mismo). Compara por
-- substring (no exacto): confirmado en juego que una entrada en una lista
-- de dope con un nombre truncado/parcial (ej. "inspiracion" en vez de
-- "inspiracion divina") con comparacion exacta nunca matcheaba, asi que
-- siempre se recasteaba de nuevo aunque ya estuviera activo.
function Clases.tieneActivo(nombreHechizo)
  if not (gmcp and gmcp.Char and gmcp.Char.Affects and gmcp.Char.Affects.BuffYDebuff) then
    return false
  end
  local buscado = nombreHechizo:lower()
  for _, afecta in ipairs(gmcp.Char.Affects.BuffYDebuff) do
    local activo = tostring(afecta.name or ""):lower()
    if activo:find(buscado, 1, true) or buscado:find(activo, 1, true) then
      return true
    end
  end
  return false
end

-- OJO: esto es la vulnerabilidad del PERSONAJE CONECTADO (gmcp.Char.Affects
-- cuelga de gmcp.Char, no de gmcp.Char.Enemies -- GMCP no expone afectos del
-- enemigo). No sirve para lo que hacia "vulnerable al Rayo/Fuego/acido." en
-- CMUD (eso rastreaba al ENEMIGO, ver rayo_ok/fuego_ok/acido_ok en Pelea).
-- Queda disponible por si sirve para automatizar algo defensivo propio.
-- true si "palabra" (ej. "fire", "lightning", "acid") aparece en
-- gmcp.Char.Affects.vulnerable. Usa find porque el server manda codigos de
-- color tipo "{Wlight{x" mezclados con el texto.
function Clases.esVulnerableA(palabra)
  if not (gmcp and gmcp.Char and gmcp.Char.Affects and gmcp.Char.Affects.vulnerable) then
    return false
  end
  for _, v in ipairs(gmcp.Char.Affects.vulnerable) do
    if tostring(v):find(palabra, 1, true) then
      return true
    end
  end
  return false
end

-- Lanza cada hechizo de "lista" (tabla de nombres) sobre "obj" (o sobre uno
-- mismo si obj es vacio). Equivalente al #FORALL @dopesXXX { cast '%i' } de
-- CMUD, usado por dopem/doper/dopeo -- MEJORADO respecto al original: si es
-- sobre uno mismo, salta los hechizos que gmcp.Char.Affects.BuffYDebuff dice
-- que ya estan activos (esto era lo que el "dope" generico de CMUD queria
-- hacer llamando a "dope_continuar", una funcion que nunca se definio).
function Clases.dopar(lista, obj)
  if not lista or #lista == 0 then
    cecho(string.format("<red>No hay hechizos definidos para dopar la clase '%s' todavia.\\n", tostring(clase)))
    return
  end
  if obj == "" or obj == nil then
    cecho("<cyan>Dopando a self\\n")
    for _, hechizo in ipairs(lista) do
      if Clases.tieneActivo(hechizo) then
        cecho("<gray>Ya activo, salteado: " .. hechizo .. "\\n")
      else
        cecho("<cyan>Dopando: " .. hechizo .. "\\n")
        send("cast '" .. hechizo .. "'")
      end
    end
  else
    -- No podemos ver los afectos de otro personaje por GMCP, asi que a un
    -- objetivo se le castea la lista completa (igual que el dopem/doper/dopeo
    -- original de CMUD).
    cecho(string.format("<cyan>Dopando a %s\\n", obj))
    for _, hechizo in ipairs(lista) do
      cecho(string.format("<cyan>Dopando: %s a %s\\n", hechizo, obj))
      send("cast '" .. hechizo .. "' " .. obj)
    end
  end
end

-- ================================================================
-- Listas de dope por clase (Clases.dopes[clase]) + persistencia, para poder
-- agregar/sacar hechizos con "addspell"/"removespell" sin tener que
-- reinstalar el paquete cada vez que subis de nivel y aprendes uno nuevo.
-- ================================================================
Clases.dopes = Clases.dopes or {}
Clases.dopesArchivo = getMudletHomeDir() .. "/petria_dopes.lua"

function Clases.guardarDopes()
  table.save(Clases.dopesArchivo, Clases.dopes)
end

function Clases.cargarDopesGuardados()
  local ok, cargado = pcall(table.load, Clases.dopesArchivo)
  if ok and type(cargado) == "table" then
    for claseGuardada, lista in pairs(cargado) do
      Clases.dopes[claseGuardada] = lista
    end
  end
end

-- Se carga ahora; los scripts de cada clase (Mago, Ranger, Seguidores...)
-- usan "Clases.dopes.X = Clases.dopes.X or {lista por defecto}" mas abajo,
-- asi que si ya habia algo guardado en disco para esa clase, se respeta, y
-- si no, cae a la lista de fabrica.
Clases.cargarDopesGuardados()

function ClasesActualizarClaseGMCP()
  if gmcp and gmcp.Char and gmcp.Char.Base and gmcp.Char.Base.class then
    -- gmcp.Char.Base.class trae el nombre completo (ej. "seguidores_de_Oteren"),
    -- pero Clases usa la clave corta ("seguidores"). CMUD hacia este mismo
    -- corte automaticamente porque su wildcard %w paraba en el "_". Se
    -- replica cortando en el primer "_".
    clase = gmcp.Char.Base.class:lower():match("^[^_]+")
  end
end

registerAnonymousEventHandler("gmcp.Char.Base", "ClasesActualizarClaseGMCP")

-- Por si GMCP ya trajo los datos antes de instalar este paquete
ClasesActualizarClaseGMCP()

-- "empalar" (SK063): "asesino guerrero paladin seguidores_de_oteren" segun
-- el helpfile en juego -- paladin no es una clase migrada aca, se ignora.
-- El helpfile aclara que es similar a apunalar: solo funciona con el
-- objetivo al maximo de vida o dormido, salvo que se combine con emboscar.
-- Por eso "k" solo la dispara como apertura (en_combate en 0/nil,
-- actualizado por GMCP en Pelea_Core), nunca en rondas siguientes.
-- OJO: en_combate arranca en 0, no nil/false -- y en Lua "0" es verdadero.
-- El chequeo tiene que ser "en_combate and en_combate ~= 0", nunca
-- "not en_combate" solo (ver resto de Pelea, que ya usa ese patron).
Clases.clasesConEmpalar = { guerrero = true, asesino = true, seguidores = true }

-- Cambia a una lanza para empalar y vuelve a las armas configuradas con
-- "setarma"/"setsegun" en el GUI oficial (variables globales
-- "armaPrincipal"/"armaSecundaria", persistidas en estado_gui.lua -- no se
-- duplica esa logica aca, solo se leen). El verbo para reequipar la
-- secundaria es "segun", no "bla" (confirmado leyendo
-- DesarmePetria.recuperar del GUI, que hace lo mismo tras un desarme).
--
-- Confirmado en juego: la lanza es un arma de DOS MANOS -- "bla lanza" con
-- la secundaria todavia puesta da "No puedes usar un arma de dos manos
-- llevando arma secundaria." y la lanza nunca queda blandida, asi que
-- "empalar" y despues "gua lanza" fallan en cascada. No alcanza con
-- confiar en que la principal se descuelgue sola: se guardan las dos
-- explicitamente ANTES de tocar la lanza.
function Clases.intentarEmpalar(obj)
  if armaPrincipal and armaPrincipal ~= "" then
    send("gua " .. armaPrincipal)
  end
  if armaSecundaria and armaSecundaria ~= "" then
    send("gua " .. armaSecundaria)
  end
  send("get lanza moch")
  send("bla lanza")
  send("empalar " .. obj)
  send("gua lanza")
  send("bla " .. (armaPrincipal or ""))
  if armaSecundaria and armaSecundaria ~= "" then
    send("segun " .. armaSecundaria)
  end
end

-- Despacha al ataque de la clase conectada (Clases[clase].ataque). Comun a
-- "k" y "kk" -- la unica diferencia entre esos dos alias es si intentan
-- empalar antes o no.
function Clases.despacharAtaque(obj)
  if clase and Clases[clase] and Clases[clase].ataque then
    Clases[clase].ataque(obj)
  else
    cecho(string.format("<red>?? Clase desconocida: %s\\n", tostring(clase)))
    send("mata " .. obj)
    send("espi")
  end
end
'''
make_script(clases_group, "Clases_Core", core_script)

guerrero_group = make_script_group(clases_group, "Guerrero")
make_script(guerrero_group, "Guerrero", '''Clases.guerrero = {
  ataque = function(obj)
    send("mata " .. obj)
    send("espi")
  end,
  recall = function()
    Clases.sendSeq("s", "s", "e", "e", "s", "e", "s")
  end,
  -- Sin lista de fabrica (CMUD no tenia dope para esta clase). Queda vacia
  -- hasta que uses "addspell" -- asi el comando "dope" funciona apenas
  -- agregues el primer hechizo, sin tener que tocar el paquete.
  dope = function(obj)
    Clases.dopar(Clases.dopes.guerrero, obj)
  end,
}''')

mago_group = make_script_group(clases_group, "Mago")
make_script(mago_group, "Mago", '''-- Lista de fabrica (original de CMUD, var StringList "dopesmago").
-- "dopesmago1" (variante corta) existia en CMUD pero no la usaba ningun
-- alias migrado -- no se trajo. Con "or": si "addspell"/"removespell" ya
-- guardaron algo para esta clase en petria_dopes.lua, Clases_Core lo carga
-- en Clases.dopes.mago ANTES de que este script corra, y se respeta esa
-- version en vez de pisarla con la de fabrica.
Clases.dopes.mago = Clases.dopes.mago or {
  "acelerar", "antifuego", "bendita niebla", "buen aura", "clon sombras",
  "deflexion", "detectar invisibilidad", "detectar magia", "detectar oculto",
  "escudo", "escudo de hielo", "fase magica", "fuerza colosal", "gatovision",
  "invisibilidad", "piel de dragon", "piel de piedra", "proteccion",
  "proteccion divina", "santuario", "traspasar", "vision verdadera", "volar",
  "contra",
}

Clases.mago = {
  ataque = function(obj)
    send("c fuente")
    send("c 'debilidad rayo' " .. obj)
    send("c 'debilidad acida' " .. obj)
    send("c 'aliento tormentoso' " .. obj)
    send("c golpe " .. obj)
    send("c torme")
    send("c dilu")
  end,
  engancha = function(obj)
    send("c fuente")
    send("can " .. obj)
    send("mata " .. obj)
  end,
  recall = function()
    Clases.sendSeq("s", "s", "w", "w", "s", "e", "s", "e")
  end,
  dope = function(obj)
    Clases.intentarAstucia()
    send("c anti bolsillo")
    Clases.dopar(Clases.dopes.mago, obj)
  end,
}''')

ladron_group = make_script_group(clases_group, "Ladron")
make_script(ladron_group, "Ladron", '''Clases.ladron = {
  ataque = function(obj)
    send("robar oro " .. obj)
    send("esconder")
    send("ocultar")
  end,
  engancha = function(obj)
    send("co " .. obj)
  end,
  recall = function()
    Clases.sendSeq("s", "s", "s", "e", "s", "e", "s")
  end,
  dope = function(obj)
    Clases.dopar(Clases.dopes.ladron, obj)
  end,
}''')

ranger_group = make_script_group(clases_group, "Ranger")
make_script(ranger_group, "Ranger", '''-- Lista de fabrica (original de CMUD, var StringList "dopesranger").
Clases.dopes.ranger = Clases.dopes.ranger or {
  "volar", "niebla", "piel", "espiritu", "bendecir",
  "detectar invisibilidad", "totem animal buho",
}

Clases.ranger = {
  ataque = function(obj)
    send("c raices " .. obj)
  end,
  engancha = function(obj)
    send("c raices " .. obj)
  end,
  recall = function()
    Clases.sendSeq("s", "nore", "n", "w")
  end,
  dope = function(obj)
    send("traga santu")
    send("c anti bolsillo")
    send("fuego")
    send("c 'totem animal buho'")
    Clases.dopar(Clases.dopes.ranger, obj)
  end,
}''')

asesino_group = make_script_group(clases_group, "Asesino")
make_script(asesino_group, "Asesino", '''Clases.asesino = {
  ataque = function(obj)
    send("corte_artero " .. obj)
    send("mata " .. obj)
    send("espi")
    send("zancadilla")
  end,
  recall = function()
    -- Ruta original de CMUD: ".3sw2swse" = 3xsuroeste + 2xsuroeste + 1xsureste.
    -- Expandida a pasos cardinales n/s/e/w (confirmados validos) en vez de
    -- mandar la notacion con "." de CMUD, que en este juego dispara un grito.
    Clases.sendSeq("s", "w", "s", "w", "s", "w", "s", "w", "s", "w", "s", "e")
  end,
  dope = function(obj)
    Clases.dopar(Clases.dopes.asesino, obj)
  end,
}''')

druida_group = make_script_group(clases_group, "Druida")
make_script(druida_group, "Druida", '''Clases.druida = {
  ataque = function(obj)
    send("mata " .. obj)
    send("c rayo")
  end,
  recall = function()
    Clases.sendSeq("s", "suro")
  end,
  dope = function(obj)
    Clases.dopar(Clases.dopes.druida, obj)
  end,
}''')

seguidores_group = make_script_group(clases_group, "Seguidores")
make_script(seguidores_group, "Seguidores", '''-- "dopesoteren" no existia como variable en el CMUD original (el alias
-- "dopeo" la usaba pero nunca se definio en ningun lado -- ya estaba roto
-- alla). Lista armada a partir del comando "spells" en juego (personaje
-- seguidores_de_Oteren), quedandonos con los autobuffs persistentes y
-- dejando afuera curas puntuales, deteccion y utilidad situacional.
Clases.dopes.seguidores = Clases.dopes.seguidores or {
  "acelerar", "antifuego", "bendecir", "detectar invisibilidad",
  "escudo luz", "fuerza colosal", "gatovision", "inspiracion divina",
  "luz protectora", "proteccion infernal", "proteccion sagrada",
  "santuario", "volar",
}

Clases.seguidores = {
  ataque = function(obj)
    -- "empalar" ya no va suelto aca: lo dispara "k" antes de llamar a
    -- ataque() (ver Clases.intentarEmpalar en Clases_Core), con el cambio
    -- de arma a lanza que esto nunca hacia.
    send("cocear " .. obj)
    send("mata " .. obj)
    send("espi")
  end,
  recall = function()
    -- alias original en CMUD se llamaba "coteren", no "cseguidores".
    -- Ruta original ".3s4ese" = 3xs + 4xe + 1xsureste, expandida a pasos
    -- cardinales (ver nota sobre "." = gritar en este juego).
    Clases.sendSeq("s", "s", "s", "e", "e", "e", "e", "s", "e")
  end,
  dope = function(obj)
    Clases.intentarAstucia()
    send("c anti bolsillo")
    Clases.dopar(Clases.dopes.seguidores, obj)
  end,
}''')

# ---------- Scripts/Petria/Pelea ----------
pelea_script_group = make_script_group(petria_script_group, "Pelea")

pelea_core_script = '''-- ================================================================
-- PELEA - PetriaMUD (migrado literal desde CMUD 03-Pelea)
-- ================================================================
-- Variables globales que usan los triggers/alias de Pelea. Todo sin
-- reclasificar todavia por clase (a proposito, ver conversacion) --
-- cuando se asocie cada trigger a su clase, esto se puede repartir
-- dentro de Clases/<clase>.
-- ================================================================

en_combate = en_combate or 0
curando = curando or 0
cd_veneno = cd_veneno or 0
cd_guardia = cd_guardia or 0
enemigo_pct = enemigo_pct or 0
enemigoNombre = enemigoNombre or ""
enemigoNivel = enemigoNivel or 0
qcomm = qcomm or 0
ultima_skill = ultima_skill or ""
rasOBJ = rasOBJ or ""
ir_Obj = ir_Obj or ""
acosado = acosado or ""

-- WoF (Guerra de Facciones) y PK: apagados por defecto. Sus triggers
-- comparten patrones de texto con el combate PvE normal (confirmado en
-- juego: "cegados por la suciedad" disparaba huir x3 de WoF ademas de la
-- zancadilla normal). Activar solo cuando realmente estes en ese modo.
if wofActivo == nil then wofActivo = false end
if pkActivo == nil then pkActivo = false end

-- Defensa/alertas (ver analisis de un ataque de jugador real: "Someone")
if recallBloqueado == nil then recallBloqueado = false end
if gargantaCortada == nil then gargantaCortada = false end

-- Banner visual fuerte para que algo importante no pase desapercibido.
-- Sin sonido: Mudlet soporta playSoundFile(ruta) si en algun momento se
-- quiere sumar un audio, pero no hay ningun archivo de sonido en este
-- paquete todavia.
function Pelea.alerta(mensaje)
  local raya = "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  cecho(string.format(
    "\\n<red:yellow><bold>%s\\n  %s\\n%s\\n\\n",
    raya, mensaje, raya
  ))
end

-- flags de ATAQUES (mago)
rayo_ok = rayo_ok or 0
fuego_ok = fuego_ok or 0
acido_ok = acido_ok or 0

-- Nombres de hechizo que usan cast00/cast01/cast02. Del CMUD original solo
-- estaban definidos ataque00 y ataque01; ataque02 no existia (posible resto
-- sin usar) -- queda vacio hasta que confirmes cual va ahi.
ataque00 = ataque00 or "golpe"
ataque01 = ataque01 or "aliento tormentoso"
ataque02 = ataque02 or ""

-- Lista de amigos para WoF (equivalente a la StringList @WoFriends de CMUD).
-- Set en lugar de lista: WoFriends["Nombre"] = true / WoFriends["Nombre"] = nil
WoFriends = WoFriends or { KittySoul = true }

-- ================================================================
-- Timers de recast (aliento tormentoso, golpe acido, rayo poderoso) que se
-- auto-cancelan al terminar el combate -- antes quedaban corriendo y podian
-- disparar un recast sin objetivo despues de matar/huir (confirmado en un
-- combate real: 3 prompts "Invocar el hechizo sobre quien?" justo despues
-- de "ESTA MUERTO"). El chequeo de en_combate adentro del timer no alcanza
-- porque puede alcanzar a dispararse en la ventana de carrera justo cuando
-- el combate termina; cancelar el timer directamente es mas robusto.
-- ================================================================
Pelea = Pelea or {}
Pelea.timersPendientes = Pelea.timersPendientes or {}

function Pelea.programarSiEnCombate(segundos, fn)
  local id
  id = tempTimer(segundos, function()
    Pelea.timersPendientes[id] = nil
    if en_combate and en_combate ~= 0 then
      fn()
    end
  end)
  Pelea.timersPendientes[id] = true
  return id
end

function Pelea.cancelarTimersPendientes()
  for id, _ in pairs(Pelea.timersPendientes) do
    killTimer(id)
  end
  Pelea.timersPendientes = {}
end

function ResetAliento()
  rayo_ok = 0
  fuego_ok = 0
  acido_ok = 0
  cecho("<cyan>Flags de debilidad reiniciados.\\n")
end

-- ================================================================
-- Auto-heal y tracking de enemigo via GMCP (en vez de parsear texto)
-- ================================================================

function PeleaActualizarVitalsGMCP()
  if not (gmcp and gmcp.Char and gmcp.Char.Vitals) then return end
  local v = gmcp.Char.Vitals
  HPcur = tonumber(v.hp)
  HPmax = tonumber(v.maxhp)
  if not HPcur or not HPmax or HPmax <= 0 then return end
  HPpct = math.floor((HPcur * 100) / HPmax)

  if not curando or curando == 0 then
    if HPpct < 35 then
      send("traga sa"); send("traga sa"); send("traga sa")
      curando = 1
      tempTimer(3, function() curando = 0 end)
    elseif HPpct < 55 then
      send("traga sa"); send("traga sa")
      curando = 1
      tempTimer(3, function() curando = 0 end)
    elseif HPpct < 75 then
      send("traga sa")
      curando = 1
      tempTimer(3, function() curando = 0 end)
    end
  end
end
registerAnonymousEventHandler("gmcp.Char.Vitals", "PeleaActualizarVitalsGMCP")

function PeleaActualizarEnemigoGMCP()
  if not (gmcp and gmcp.Char and gmcp.Char.Enemies and gmcp.Char.Enemies[1] and gmcp.Char.Enemies[1][1]) then
    en_combate = 0
    enemigo_pct = 0
    pcall(function() Pelea.cancelarTimersPendientes() end)
    return
  end
  local e = gmcp.Char.Enemies[1][1]
  en_combate = 1
  enemigoNombre = e.name
  enemigoNivel = tonumber(e.level)
  local ehp, emax = tonumber(e.hp), tonumber(e.maxhp)
  if ehp and emax and emax > 0 then
    enemigo_pct = math.floor((ehp * 100) / emax)
  end
end
registerAnonymousEventHandler("gmcp.Char.Enemies", "PeleaActualizarEnemigoGMCP")

-- Actualiza si ya hay datos GMCP cacheados desde antes de instalar el paquete
PeleaActualizarVitalsGMCP()
PeleaActualizarEnemigoGMCP()
'''
make_script(pelea_script_group, "Pelea_Core", pelea_core_script)

# ---------- KeyPackage ----------
# El primer intento (punto del numerico -> traga sabia, keyCode 46) no
# funciono: en este sistema el numerico manda los codigos de "navegacion"
# (Insert/Delete/Home/End/etc), no los digitos/simbolos ASCII normales --
# confirmado leyendo las teclas reales que el usuario ya tenia armadas a
# mano en Mudlet (capturadas por la UI, no adivinadas):
#   sanar       -> numerico 0   -> Qt::Key_Insert = 16777222
#   recall      -> tecla End    -> 16777232 (sin KeypadModifier)
#   Savia verde -> numerico "." -> Qt::Key_Delete = 16777223
# Se migran esas 3 al paquete (con sus keyCodes reales) para que:
#  1) sobrevivan a updatepkg (antes vivian sueltas en el perfil, en riesgo
#     de perderse si el usuario las tenia anidadas dentro de la carpeta de
#     teclas de este mismo paquete);
#  2) se sincronicen a la otra PC via git, como el resto.
key_pkg = ET.SubElement(root, "KeyPackage")

def make_key_group(parent, name):
    g = ET.SubElement(parent, "KeyGroup", {"isActive": "yes", "isFolder": "yes"})
    ET.SubElement(g, "name").text = name
    ET.SubElement(g, "packageName").text = name
    ET.SubElement(g, "script").text = ""
    ET.SubElement(g, "command").text = ""
    ET.SubElement(g, "keyCode").text = "0"
    ET.SubElement(g, "keyModifier").text = "0"
    return g

def make_key(parent, name, key_code, key_modifier, script):
    k = ET.SubElement(parent, "Key", {"isActive": "yes", "isFolder": "no"})
    ET.SubElement(k, "name").text = name
    ET.SubElement(k, "packageName").text = ""
    ET.SubElement(k, "script").text = script
    ET.SubElement(k, "command").text = ""
    ET.SubElement(k, "keyCode").text = str(key_code)
    ET.SubElement(k, "keyModifier").text = str(key_modifier)
    return k

QT_KEYPAD_MODIFIER = 536870912
QT_KEY_INSERT = 16777222  # numerico 0 (sin numlock)
QT_KEY_DELETE = 16777223  # numerico "." (sin numlock)
QT_KEY_END = 16777232

# Teclado Mac (sin numerico fisico): equivalentes capturados a mano en la
# UI de Mudlet en la Mac (leidos directo del profile.xml, mismo metodo que
# con las de la HP Pavilion arriba - no adivinados).
QT_KEY_BRACELEFT = 123   # "["/"{" fisico
QT_KEY_BRACERIGHT = 125  # "]"/"}" fisico
QT_KEY_QUESTIONDOWN = 191  # "¿" fisico del teclado Mac (Backspace no sirve:
# Mudlet lo usa para editar el texto de la linea de comando, nunca llega
# al sistema de Key Bindings - confirmado probando en juego)

petria_key_group = make_key_group(key_pkg, "Petria-Rhuna")
teclas_key_group = make_key_group(petria_key_group, "Teclas")
make_key(teclas_key_group, "sanar", QT_KEY_INSERT, QT_KEYPAD_MODIFIER, 'send("traga sana")')
make_key(teclas_key_group, "recall", QT_KEY_END, 0, 'send("recall")\nsend("n")\nsend("curar")')
make_key(teclas_key_group, "Savia verde", QT_KEY_DELETE, QT_KEYPAD_MODIFIER, 'send("traga savia")')
make_key(teclas_key_group, "MAC-Sanar", QT_KEY_BRACELEFT, 0, 'send("traga sana")')
make_key(teclas_key_group, "MAC-SaviaVerde", QT_KEY_BRACERIGHT, 0, 'send("traga savia")')
make_key(teclas_key_group, "MAC-Recall", QT_KEY_QUESTIONDOWN, 0, 'send("recall")\nsend("n")\nsend("curar")')

# ---------- VariablePackage ----------
var_pkg = ET.SubElement(root, "VariablePackage")
ET.SubElement(var_pkg, "HiddenVariables")

indent(root)
tree = ET.ElementTree(root)
# Ruta relativa a este script (no al home de una maquina en particular), asi
# el script funciona igual clonado en cualquier PC.
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Petria-Rhuna.xml")

with open(out_path, "wb") as f:
    f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE MudletPackage>\n')
    tree.write(f, encoding="unicode".encode() if False else "utf-8", xml_declaration=False)

print("OK ->", out_path)
