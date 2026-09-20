import os
import time
import xml.etree.ElementTree as ET

# URL para "updatepkg" (vive en el paquete separado Petria-Rhuna-Updater,
# ver el final de este script): raw.githack.com sobre "main" (rama
# mutable), NO jsdelivr y NO un commit fijo.
#
# Historia (por que no las otras dos opciones):
# - Commit fijo (@<sha>/Petria-Rhuna.xml en jsdelivr): confiable en cada
#   prueba puntual, pero mal diseno de fondo -- el Updater se instala UNA
#   vez y nunca se vuelve a tocar (ese es su objetivo, sobrevivir a fallas
#   del paquete principal). Si su URL apunta a un commit fijo, ese commit
#   queda CONGELADO para siempre salvo que el usuario reinstale el Updater
#   despues de cada push -- contradice el "nunca hace falta tocarlo".
# - jsdelivr con "@main" (rama mutable): confirmado en juego, repetidas
#   veces, que jsdelivr puede tardar minutos en sincronizar un push nuevo
#   (bastante mas que la propagacion normal esperada) -- incluso con purge
#   inmediato despues de cada push. Comparado en vivo con raw.githack.com
#   y rawcdn.githack.com sobre el mismo push: ambos ya mostraban el ultimo
#   build mientras jsdelivr @main seguia atascado en el anterior.
# raw.githack.com esta pensado justo para esto (contenido que cambia
# seguido, poca cache) -- por eso se eligio en vez de la variante
# "produccion" rawcdn.githack.com (mas cacheada, pensada para contenido
# estable).
JSDELIVR_URL = "https://raw.githack.com/z0y1b0t/petria-mudlet/main/Petria-Rhuna.xml"
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

# --- Estados del prompt (%S): V volando, I invisible, A adrenalina, M maldito,
# G golpetazo... Confirmado en logs: "V I", "M A", "G A". Linea ejemplo:
#   < 3024hp[3024hp] 1340m[1340m] 1270mv[1270mv]>  V I  Lv4800 >
make_trigger(
    petria_trig_group, "Estados del prompt (letras de %S)",
    r'''local letras = matches[2] or ""
Petria.estadosPrompt = letras
Petria.enGolpetazo = letras:find("G", 1, true) ~= nil''',
    [r"mv\[\d+mv\]>\s+(.*?)\s*Lv\d+ >"],
)

# --- Modo torneo: contadores del prompt y huidas logradas ---
# "Poc: N Per: N Var: N" del prompt = pociones, pergaminos y varitas USADOS.
make_trigger(
    petria_trig_group, "Torneo: contadores del prompt",
    r'''Petria.poc = tonumber(matches[2]) or Petria.poc
Petria.per = tonumber(matches[3]) or Petria.per
Petria.var = tonumber(matches[4]) or Petria.var
Petria.pocPend = 0
Petria.varPend = 0
Petria.huidasPend = 0''',
    [r"Poc: (\d+) Per: (\d+) Var: (\d+)"],
)
make_trigger(
    petria_trig_group, "Torneo: huida lograda",
    r'''Petria.huidas = (Petria.huidas or 0) + 1
if Petria.torneo then
  cecho(string.format("<yellow>[TORNEO] huidas: %d/3\n", Petria.huidas))
end''',
    [r"Logras HUIR!"],
)

# --- Autodope: recastea buffs propios apenas se van despejando ---
# Asociado a mano contra la lista de "spells" del personaje (seguidores_de
# Oteren) + los mensajes de "se te pasa el efecto" que se ven en juego.
# "Comienzas a descongelarte." quedo afuera: no matchea con nada de la
# lista de spells (podria ser el fin de un efecto hostil, no un buff propio
# para recastear) -- confirmar antes de agregarlo.
autodope_trig_group = make_trigger_group(petria_trig_group, "Autodope")
# Confirmado en juego (log de PvP contra un disipar magia): el servidor manda
# TODOS los mensajes de "se te pasa el efecto" pegados en un solo bloque, sin
# salto de linea entre ellos, y ademas corta a ~100 columnas en medio de
# frases ("Despacito dejas de / levitar...", "Tu proteccion contra / el mal
# mengua"). Con patrones anclados (^...$) ninguno matcheaba. Por eso van sin
# anclas y con un fragmento corto que sobrevive al corte. Ademas solo recasteo
# si el hechizo esta en el dope de la clase (Clases.reponer).
make_trigger(autodope_trig_group, "Santuario se despeja", 'Clases.reponer("santuario", "c santuario")', [r"Los efectos de Santuario"])
make_trigger(autodope_trig_group, "Inspiracion divina se va", 'Clases.reponer("inspiracion", "c inspiracion")', [r"tu inspiracion divina"])
make_trigger(autodope_trig_group, "Fuerza colosal se va (mas debil)", 'Clases.reponer("fuerza colosal", "c \'fuerza colosal\'")', [r"Te sientes mas debil\."])
make_trigger(autodope_trig_group, "Proteccion infernal mengua", 'Clases.reponer("proteccion infernal", "c \'proteccion infernal\'")', [r"el mal mengua"])
make_trigger(autodope_trig_group, "Escudo de luz desaparece", 'Clases.reponer("escudo luz", "c \'escudo luz\'")', [r"El escudo de luz que te rodeaba"])
make_trigger(autodope_trig_group, "Luz protectora desaparece", 'Clases.reponer("luz protectora", "c \'luz protectora\'")', [r"Los rayos de luz que te rodeaban"])
make_trigger(autodope_trig_group, "Proteccion sagrada se desvanece", 'Clases.reponer("proteccion sagrada", "c \'proteccion sagrada\'")', [r"Tu proteccion sagrada se desvanece"])
make_trigger(autodope_trig_group, "Acelerar termina (ritmo normal)", 'Clases.reponer("acelerar", "c acelerar")', [r"Ya vuelves a recuperar tu ritmo normal"])
make_trigger(autodope_trig_group, "Volar termina", 'Clases.reponer("volar", "c volar")', [r"Despacito dejas de"])
# "Ya no ves ni tres en un burro en la oscuridad." salio en el mismo bloque de
# un cancelacion rival, entre los buffs de dope; por lo de "oscuridad" lo
# tomo como el fin de gatovision (inferido, no confirmado aislado).
make_trigger(autodope_trig_group, "Gatovision termina", 'Clases.reponer("gatovision", "c gatovision")', [r"Ya no ves ni tres en un burro"])
# "Ya no ves objetos invisibles ni na de na." salio en un cancelacion propio y
# no habia trigger: detectar invisibilidad quedaba sin recastear.
make_trigger(autodope_trig_group, "Detectar invisibilidad termina", 'Clases.reponer("detectar invisibilidad", "c \'detectar invisibilidad\'")', [r"Ya no ves objetos invisibles"])
make_trigger(autodope_trig_group, "Bendecir termina", 'Clases.reponer("bendecir", "c bendecir")', [r"La bendicion ya no tiene efecto"])
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
# Se quito el "huir" de "SANGRAS A LO BESTIA": el sangrado viene de procs de
# armas rivales (PvP contra Alien: lanza "sangrante"), huir no lo cura, y con
# el rival persiguiendo fallo/no sirvio. La cura usa Petria.sanar() (en la
# Torre "traga" teletransporta al pozo) y el server manda varias lineas de
# sangrado por ronda, asi que se deduplica a 1 cada segundo.
make_trigger(
    pelea_trig_group, "Perdiendo mucha sangre: curar",
    'if cd_sangre == 1 then return end\n'
    'cd_sangre = 1\n'
    'tempTimer(1, function() cd_sangre = 0 end)\n'
    'Petria.sanar()',
    [r"(?i)¡?¡?EST[aáA]S PERDIENDO DEMASIADA SANGRE!!"],
)
# Linea de estado del enemigo que el server manda UNA vez al final de cada
# ronda de melee (vista en los logs: "X tiene algunos cortes y magulladuras.",
# "esta bastante herido", "esta en mal estado", "esta malherido", "nota que
# la muerte le llama", "esta en una excelente condicion"). Si aparece otra
# variante en algun mob, esa ronda simplemente no lanza (nunca lanza de mas).
# La linea de estado del enemigo solo sale durante TU combate. En el log de las
# hormigas de la Reina en_combate quedaba en 0 (lo pone en 1 solo el evento GMCP
# Char.Enemies, y "ESTA MUERTO !!" lo baja a 0 con cada hormiga): el trigger de
# ronda no lanzo ni un hechizo y "k" volvio a empalar en plena pelea. Aqui se
# marca en_combate = 1 con cada linea de estado, y de paso se vigila el mv.
make_trigger(
    pelea_trig_group, "Estado del enemigo: en combate",
    r'''en_combate = 1
local v = gmcp and gmcp.Char and gmcp.Char.Vitals
local mv, mvmax = v and tonumber(v.move), v and tonumber(v.maxmove)
if mv and mvmax and mvmax > 0 and mv < mvmax * 0.25 and (not cd_mv or cd_mv == 0) then
  local mana = tonumber(v.mana)
  if not mana or mana >= 50 then
    send("c refrescar")
    cd_mv = 1
    tempTimer(3, function() cd_mv = 0 end)
  end
end''',
    [r"^(.+?) (?:tiene algunos cortes|est[aá] bastante herido|est[aá] en mal estado|est[aá] malherido|nota que la muerte le llama|est[aá] en una excelente condici[oó]n)"],
)
# Confirmado en juego (hormigas de la Reina): ira divina contra un mob no
# maligno responde "X no es ningun ser maligno...." y gasta mana y una ronda.
# Se recuerda el tipo de mob y la ronda deja de lanzarle hechizos.
make_trigger(
    pelea_trig_group, "Objetivo no maligno: dejar de lanzar",
    r'''local kw = Petria.palabraClave(matches[2])
if kw and not Petria.noMalignos[kw] then
  Petria.noMalignos[kw] = true
  cecho("<yellow>Ronda: '" .. kw .. "' no es maligno; los hechizos de ataque no le hacen nada, dejo de lanzarle (aa limpiar para olvidar).\n")
end''',
    [r"^(.+?) no es ning[uú]n ser maligno"],
)
# Confirmado en juego (un "equipaje"): "El equipaje es inmune a tu ira divina!"
# (tambien a empalar, relampago luminoso y rafaga gelida). La ronda seguia
# lanzando ira divina cada ronda. Se recuerda por tipo de mob y hechizo.
make_trigger(
    pelea_trig_group, "Inmune a un hechizo de ronda: probar otro",
    r'''local kw = Petria.palabraClave(matches[2])
local ataque = (matches[3] or ""):lower()
if kw and (ataque == "ira divina" or ataque == "rayo de sinceridad" or ataque == "destruir maldad") then
  Petria.inmunes[kw] = Petria.inmunes[kw] or {}
  if not Petria.inmunes[kw][ataque] then
    Petria.inmunes[kw][ataque] = true
    cecho("<yellow>Ronda: '" .. kw .. "' es inmune a " .. ataque .. "; pruebo con otro hechizo (aa limpiar para olvidar).\n")
  end
end''',
    [r"^(.+?) es inmune a tu (.+)!\s*$"],
)
# PvP: golpetazo deja al rival sin poder tomar pociones (confirmado por el
# jugador). Conviene mandarlo cuando ya esta medio bajo de HP: un Mago no se
# puede curar de otra forma, mientras que un Oteren sigue con "c sanar". Solo
# contra JUGADORES: su nombre sale de una palabra y sin articulo ("Needle"),
# los mobs traen articulo o varias palabras. El trigger ya existente
# "Recuperado de golpetazo" lo reaplica cuando se le acaba el efecto.
# Mensaje confirmado en juego cuando TE aplican golpetazo: "!X te hace ver las
# estrellas con un poderoso golpetazo!". El golpetazo impide tomar pociones
# (dato del jugador). La condicion real la da el afecto "golpetazo" por GMCP
# (Petria.sinPociones); aqui solo se marcan 4 s de respaldo y se avisa.
make_trigger(
    pelea_trig_group, "Golpetazo recibido: sin pociones, curar con hechizo",
    r'''Petria.sinPocionesHasta = os.time() + 4
Petria.enGolpetazo = true
if Petria.puedeSanarConHechizo() then
  cecho("<yellow>Golpetazo: sin pociones unos segundos, me curo con c sanar\n")
end''',
    [r"te hace ver las estrellas con un poderoso golpetazo"],
)
# Confirmado por el jugador: al recuperarte tu del golpetazo, lo unico que
# muestra el juego es "!Bash!". A partir de ahi ya puedes tomar pociones.
make_trigger(
    pelea_trig_group, "Recuperado del golpetazo propio: pociones otra vez",
    r'''Petria.sinPocionesHasta = nil
Petria.enGolpetazo = false
Petria.golpetazoFinAt = os.time()
cecho("<green>Golpetazo terminado: ya puedes tomar pociones\n")''',
    [r"^[!¡]Bash!\s*$"],
)
make_trigger(
    pelea_trig_group, "PvP: golpetazo si el rival esta bajo de HP",
    r'''if Petria.golpetazoPvP == false then return end
if cd_golpetazo == 1 then return end
local nombre = matches[2] or ""
if not nombre:match("^[%w_]+$") then return end
local l = (line or ""):lower()
if l:find("bastante herido", 1, true) or l:find("mal estado", 1, true)
   or l:find("malherido", 1, true) or l:find("la muerte le llama", 1, true) then
  cd_golpetazo = 1
  tempTimer(8, function() cd_golpetazo = 0 end)
  send("golpetazo")
end''',
    [r"^(.+?) (?:tiene algunos cortes|est[aá] bastante herido|est[aá] en mal estado|est[aá] malherido|nota que la muerte le llama|est[aá] en una excelente condici[oó]n)"],
)
make_trigger(
    pelea_trig_group, "Ronda: lanzar hechizo",
    r'''if not Petria.rondaActiva then return end
if cd_ronda == 1 then return end
local completa = gmcp and gmcp.Char and gmcp.Char.Base and gmcp.Char.Base.class
if not (completa and tostring(completa):lower():find("oteren", 1, true)) then return end
local mana = gmcp and gmcp.Char and gmcp.Char.Vitals and tonumber(gmcp.Char.Vitals.mana)
if mana and mana < 100 then return end
-- Con menos de 40% de mana, el rayo (20 por cast) se acaba a media pelea
-- larga; paso a destruir maldad (10 por cast, modo PVP).
local maxmana = gmcp and gmcp.Char and gmcp.Char.Vitals and tonumber(gmcp.Char.Vitals.maxmana)
if mana and maxmana and maxmana > 0 and mana < maxmana * 0.4
   and Petria.rondaHechizo == "rayo de sinceridad" then
  Petria.rondaHechizo = "destruir maldad"
  Petria.rondaAutoBajada = true
  cecho("<yellow>Ronda: mana bajo 40%, paso a PVP (destruir maldad, 10 de mana).\n")
end
-- "conjurar" toma una sola palabra de objetivo: sacar una palabra clave del
-- nombre ("El diablo ingeniero" -> "diablo").
local kw = Petria.palabraClave(matches[2])
if not kw then return end
-- Los hechizos de ataque de Oteren solo dan a seres malignos: si el juego ya
-- dijo "no es ningun ser maligno" de este tipo de mob, no gastar mana.
if Petria.noMalignos[kw] then return end
-- Si el mob es inmune al hechizo elegido, probar los otros dos (el juego dice
-- "X es inmune a tu ira divina!"); si es inmune a los tres, no lanzar.
local ciclo = {"rayo de sinceridad", "ira divina", "destruir maldad"}
local inm = Petria.inmunes[kw] or {}
local hechizo = Petria.rondaHechizo
if inm[hechizo] then
  hechizo = nil
  for _, h in ipairs(ciclo) do
    if not inm[h] then hechizo = h; break end
  end
end
if not hechizo then return end
cd_ronda = 1
tempTimer(1, function() cd_ronda = 0 end)
send("conjurar '" .. hechizo .. "' " .. kw)''',
    [r"^(.+?) (?:tiene algunos cortes|est[aá] bastante herido|est[aá] en mal estado|est[aá] malherido|nota que la muerte le llama|est[aá] en una excelente condici[oó]n)"],
)
# Confirmado en juego (PvP): sin pociones "traga sana" da "No tienes esa
# pocion." y se gastaron 4 rondas repitiendolo a 170 HP. Cae a "c sanar".
make_trigger(
    pelea_trig_group, "Sin pocion: curar con hechizo",
    'if cd_sinpocion == 1 then return end\n'
    'local hp = gmcp and gmcp.Char and gmcp.Char.Vitals and tonumber(gmcp.Char.Vitals.hp)\n'
    'local maxhp = gmcp and gmcp.Char and gmcp.Char.Vitals and tonumber(gmcp.Char.Vitals.maxhp)\n'
    'if hp and maxhp and maxhp > 0 and hp >= maxhp * 0.8 then return end\n'
    'cd_sinpocion = 1\n'
    'tempTimer(1, function() cd_sinpocion = 0 end)\n'
    'send("c sanar")',
    [r"^No tienes esa pocion\.$"],
)
make_trigger(
    pelea_trig_group, "Demasiado cansado: refrescar",
    '-- Confirmado en juego: "c refrescar" no es un comando real -- 4 rondas\n'
    '-- de 3 intentos gastaron mana sin mover el mv de 0 ni una vez. El que\n'
    '-- si funciona es "curar refre" (bare, sin "c" -- pide al curandero,\n'
    '-- mismo comando que ya usa "Menos cansado: seguir curando hasta\n'
    '-- llenar move"). Pedido explicito: mandar 1-2, no spamear -- este\n'
    '-- mensaje se repite solo en cada prompt mientras el mv siga en 0, asi\n'
    '-- que ademas se agrega un cooldown para no pedir de nuevo cada vez\n'
    '-- que se repite el mismo mensaje.\n'
    'if not cd_cansado or cd_cansado == 0 then\n'
    '  send("curar refre")\n'
    '  send("curar refre")\n'
    '  cd_cansado = 1\n'
    '  tempTimer(6, function() cd_cansado = 0 end)\n'
    'end',
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
    '-- Confirmado en juego: faltaba el objetivo -- mandaba "c \'debilidad\n'
    '-- rayo\'" solo, sin destinatario.\n'
    'ResetAliento()\n'
    'if rasOBJ and rasOBJ ~= "" then send("c \'debilidad rayo\' " .. rasOBJ) end',
    [r"^La Debilidad Rayo deja de afectar"],
)
make_trigger(
    pelea_trig_group, "Debilidad Acida termina",
    '-- Mismo bug que "Debilidad Rayo termina": faltaba el objetivo.\n'
    'if rasOBJ and rasOBJ ~= "" then send("c \'debilidad acida\' " .. rasOBJ) end',
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
    '-- "GA01" no existe como trigger group real en este paquete (resto\n'
    '-- vestigial de CMUD, el pcall solo evita que tire error). No hace\n'
    '-- falta mandar nada mas aca: el golpe acido ya no se reintenta solo\n'
    '-- porque su propio loop de cooldown esta atado a su mensaje de EXITO\n'
    '-- (que nunca llega si es inmune), y "aliento tormentoso" (rayo) sigue\n'
    '-- pegando solo via su propio loop independiente ("Cooldown aliento\n'
    '-- tormentoso"), sin depender de este trigger -- confirmado en juego.\n'
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
    'Petria.traga("ceguera")',
    [r"^\.\.Has sido deslumbrado!!$"],
)
make_trigger(
    pelea_trig_group, "Tracker de qcomm (linea de estado)",
    "qcomm = tonumber(matches[3])",
    [r"^\|(.*)\[(\d+)\]\s*(.*)G"],
)
# Heredado de CMUD ("ha sido deslumbrado!!" -> c 'curar deslumbrar', sin
# objetivo = sobre uno mismo). Con "rayo de sinceridad" deslumbras al ENEMIGO
# y esto gastaba un cast en "No estas deslumbrado." (confirmado en juego). Se
# salta si la linea nombra a tu enemigo actual (GMCP).
make_trigger(
    pelea_trig_group, "Enemigo deslumbrado: curar",
    r'''local e = enemigoNombre and tostring(enemigoNombre):lower()
if e and e ~= "" and (line or ""):lower():find(e, 1, true) then return end
send("c 'curar deslumbrar'")''',
    [r"ha sido deslumbrado!!$"],
)
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
    '-- El original de CMUD mandaba "curar veneno" bare -- confirmado en\n'
    '-- juego que SOLO funciona con un curandero al lado. Version anterior\n'
    '-- de este trigger cambio a una pocion universal asumiendo que el\n'
    '-- hechizo (\'c "curar veneno"\') no existia para ninguna clase --\n'
    '-- INCORRECTO: confirmado en juego que Seguidores SI lo tiene (y las\n'
    '-- comillas dobles funcionan bien, "No conoces ningun hechizo" era por\n'
    '-- la clase, no por la sintaxis) -- solo Mago no. En vez de asumir por\n'
    '-- clase, intenta el hechizo primero y SOLO si falla (con ese mensaje\n'
    '-- especifico) cae a un respaldo. El respaldo depende de la zona: en\n'
    '-- Torre de la Desesperanza "traga" te teletransporta a un foso (ver\n'
    '-- Petria.enZonaSinPociones), asi que ahi se usa el "amuleto raro"\n'
    '-- (varita, 10 cargas, hechizo curar veneno -- se usa con zap, no\n'
    '-- traga, mismo patron que el puntero de autocurarse del alias "za")\n'
    '-- en vez de la pocion, para no gastar cargas limitadas fuera de la\n'
    '-- zona donde no hace falta.\n'
    'if not cd_veneno or cd_veneno == 0 then\n'
    '  cd_veneno = 1\n'
    '  tempTimer(6, function() cd_veneno = 0 end)\n'
    '  send(\'c "curar veneno"\')\n'
    '  local idFallo\n'
    '  idFallo = tempRegexTrigger("No conoces .* hechizo con ese nombre\\\\.", function()\n'
    '    if exists(idFallo, "trigger") == 1 then killTrigger(idFallo) end\n'
    '    if Petria.enZonaSinPociones() then\n'
    '      if not Petria.usaVarita() then return end\n'
    '      if Petria.armaValida(armaPrincipal) then send("gua " .. armaPrincipal) end\n'
    '      if Petria.armaValida(armaSecundaria) then send("gua " .. armaSecundaria) end\n'
    '      send("get amuleto moch")\n'
    '      send("sos amuleto")\n'
    '      send("zap self")\n'
    '      if Petria.armaValida(armaPrincipal) then send("bla " .. armaPrincipal) end\n'
    '      if Petria.armaValida(armaSecundaria) then send("segun " .. armaSecundaria) end\n'
    '    else\n'
    '      send("get karma moch")\n'
    '      Petria.traga("karma")\n'
    '    end\n'
    '  end)\n'
    '  tempTimer(1, function()\n'
    '    if exists(idFallo, "trigger") == 1 then killTrigger(idFallo) end\n'
    '  end)\n'
    'end',
    [r"Tienes retortijones y vomitas\."],
)
make_trigger(pelea_trig_group, "Recuperado de golpetazo", 'expandAlias("skill golpeta")', [r"se recupera de los efectos del golpetazo\.$"])
make_trigger(pelea_trig_group, "Transeunte resiste raices", 'send("c rai")', [r"pero un transeunte casual se resiste a ellas\.$"])
make_trigger(pelea_trig_group, "Cegados por suciedad: zancadilla", 'expandAlias("skill zancadilla")', [r"han sido cegados por la suciedad!"])
# Deslumbrado (uno mismo, no el enemigo -- eso es el trigger de arriba).
# Pedido explicito: prioridad sobre cualquier otra accion -- como Mudlet
# procesa cada trigger apenas llega la linea (no hay cola propia nuestra
# de por medio), send() acá ya sale antes que cualquier cosa que dispare
# despues en la misma pelea.
make_trigger(pelea_trig_group, "Deslumbrado: curar ya", 'send("c \'curar deslumbrar\'")', [r"Has sido deslumbrado!!"])
# Enemigo (PvE normal, no WoF/PK) huye de la pelea: lo perseguimos y
# reatacamos, en vez de dejarlo escapar. Igual patron que "Amigo WoF se va
# por una salida" (linea de abajo, esa es solo para WoFriends) pero
# generico -- se dispara si el nombre completo de quien huye (matches[2])
# contiene el keyword que le pasamos a "k"/"kk" (rasOBJ), asi no persigue
# a cualquiera que huya en la sala, solo al objetivo actual.
# Confirmado en juego: rasOBJ queda pegado del ULTIMO k/kk que usaste, sin
# importar cuanto tiempo paso ni si segui en combate -- sin el chequeo de
# en_combate, cualquier NPC de la sala cuyo nombre contuviera ese keyword
# (aunque ya no estuvieras peleando nada) te hacia salir corriendo atras
# de el, sin querer. "en_combate and en_combate ~= 0" (NO alcanza con
# "en_combate" solo -- arranca en 0, que en Lua es verdadero).
make_trigger(
    pelea_trig_group, "Enemigo huye: perseguir y reatacar",
    'local nombreCompleto, direccion = matches[2], matches[3]\n'
    'if en_combate and en_combate ~= 0 and rasOBJ and rasOBJ ~= "" and nombreCompleto:lower():find(rasOBJ:lower(), 1, true) then\n'
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
make_trigger(
    ataques_group, "Vulnerable al Acido",
    '-- Confirmado en juego (log real): el comando que realmente conecta es\n'
    '-- "c golpe" solo, sin comillas (una palabra, como "c fuente"/"c torme")\n'
    '-- -- disparo "Tu golpe acido hace..." decenas de veces asi durante toda\n'
    '-- la pelea. "c \\"golpe acido\\"" (con comillas y la palabra de mas) no\n'
    '-- es el comando real, quedaba sin usarse.\n'
    'acido_ok = 1\n'
    'send("c golpe")',
    [r"vulnerable al acido\."],
)

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
    'send("ocu")\nPetria.traga("sanar")\nsend("c sanar")\nsend("c sanar")\nsend("za")\nPetria.traga("santu")\n'
    'if rasOBJ and rasOBJ ~= "" then send("ras " .. rasOBJ) end',
    [r"^¡?Logras HUIR!  \.\.\.Cobardemente\.\.\."],
)
make_wof_trigger("Poder del oso ancestral (WoF)", 'send("espinillazo")\nPetria.huir()\nPetria.huir()', [r"^Ahora, caminas con el poder y la ferocidad del oso ancestral\.$"])
make_wof_trigger("Cegados por suciedad: huir", 'Petria.huir()\nPetria.huir()\nPetria.huir()', [r"han sido cegados por la suciedad!$"])
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

# --- Subcarpeta MonteGnomo ---
# Migracion literal de la clase "MonteGnomo" de CMUD (evento/puzzle de la
# zona Monte Gnomo): el monte tiembla -> usar la palanca -> se abre un
# panel de roca -> agarrar la chispa del nucleo -> guardarla y ocultarse
# (eds) -> 2 avisos de progreso de erupciones detenidas, cada uno te saca
# y te oculta de nuevo. El "#waitfor" de CMUD se traduce a
# Petria.esperarTexto (igual patron que pocsantu/pocionesfull).
# Pedido explicito: solo aplica si Raza: gnomo -- mismo alcance que
# "astucia gnoma" (Clases.intentarAstucia), asi que cada trigger chequea
# Petria.esGnomo() antes de hacer nada.
montegnomo_trig_group = make_trigger_group(petria_trig_group, "MonteGnomo")

def make_montegnomo_trigger(name, script, patterns):
    return make_trigger(montegnomo_trig_group, name, 'if not Petria.esGnomo() then return end\n' + script, patterns)

make_montegnomo_trigger(
    "Monte tiembla: usar palanca",
    'send("n")\nsend("usar palanca")',
    [r"^El Monte tiembla\."],
)
make_montegnomo_trigger(
    "Panel de roca abierto: agarrar chispa",
    'send("e")\n'
    'Petria.esperarTexto("Una Chispa del Nucleo flota aqui\\\\.\\\\.", function()\n'
    '  send("get chispa")\n'
    '  send("w")\n'
    '  send("s")\n'
    '  send("pon chispa moch")\n'
    '  expandAlias("eds")\n'
    'end, 15)',
    [r"^El panel de roca gira abriendo la pared Este\.$"],
)
make_montegnomo_trigger("2/3 erupciones detenidas", 'send("s")\nexpandAlias("eds")', [r"^Has detenido 2/3 erupciones\.$"])
make_montegnomo_trigger("1/3 erupciones detenidas", 'send("s")\nexpandAlias("eds")', [r"^Has detenido 1/3 erupciones\.$"])

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
    '-- Igual que kk: quitar santuario/acelerar del objetivo antes de pegar\n'
    '-- (las hormigas de la Reina traen santuario). Confirmado en juego que\n'
    '-- "can" antes de "empalar" no rompe el requisito de vida completa.\n'
    'if obj ~= "" and obj:lower() ~= "someone" then\n'
    '  expandAlias("can " .. obj)\n'
    'end\n\n'
    'if obj ~= "" and clase and Clases.clasesConEmpalar[clase] and not (en_combate and en_combate ~= 0) then\n'
    '  Clases.intentarEmpalar(obj)\n'
    'end\n\n'
    '-- Oteren: dejar encendida la ronda de hechizos (modo JEFE = rayo de\n'
    '-- sinceridad, ver alias "aa"). Si ya estaba prendida con otro modo\n'
    '-- elegido a mano se respeta; si un pelea anterior la bajo sola a PVP por\n'
    '-- poco mana, vuelve a JEFE.\n'
    'local completa = gmcp and gmcp.Char and gmcp.Char.Base and gmcp.Char.Base.class\n'
    'if completa and tostring(completa):lower():find("oteren", 1, true) then\n'
    '  if Petria.rondaAutoBajada then\n'
    '    Petria.rondaAutoBajada = false\n'
    '    Petria.rondaHechizo = "rayo de sinceridad"\n'
    '  end\n'
    '  if not Petria.rondaActiva then\n'
    '    Petria.rondaActiva = true\n'
    '    Petria.rondaHechizo = "rayo de sinceridad"\n'
    '    cecho("<cyan>Ronda: JEFE, hechizo: rayo de sinceridad\\n")\n'
    '  end\n'
    'end\n\n'
    'Clases.despacharAtaque(obj)'
)

# "kk": igual que "k" pero SIN el intento de empalar -- para cuando ya
# estas en combate (ej. te atacaron primero) y solo queres que dispare los
# ataques de la ficha de la clase, sin perder turnos cambiando a lanza.
make_alias(
    clases_alias_group, "kk", r"^kk(?: (.+))?$",
    'local obj = matches[2] or ""\n'
    '-- "kk" a secas: usar el enemigo que GMCP ya rastrea (Char.Enemies) para\n'
    '-- que igual se lance "can" (quitar santuario del rival). Solo si es un\n'
    '-- nombre de una palabra ASCII (jugador); un mob de varias palabras\n'
    '-- ("Un guardia de Clentigna") no sirve como objetivo de "can".\n'
    'if obj == "" and en_combate and en_combate ~= 0 and enemigoNombre\n'
    '   and tostring(enemigoNombre):match("^[%w_]+$") then\n'
    '  obj = tostring(enemigoNombre)\n'
    'end\n'
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
    '-- "vision verdadera" solo la tiene el dope del Mago: confirmado en juego\n'
    '-- que un Oteren recibe "No conoces ningun hechizo con ese nombre."\n'
    'if Clases.enDope("vision verdadera") and not Clases.tieneActivo("vision verdadera") then\n'
    '  send("conjurar \'vision verdadera\'")\n'
    'end\n\n'
    '-- Si el atacante esta identificado (no "Someone", que es lo que manda\n'
    '-- el server cuando no lo podes ver/detectar -- ver alerta de PK en\n'
    '-- Pelea), cancelamos lo que este canalizando via el alias "can" ya\n'
    '-- existente (reintento incluido).\n'
    'if obj ~= "" and obj:lower() ~= "someone" then\n'
    '  expandAlias("can " .. obj)\n'
    'end\n\n'
    '-- Hook opcional por clase: hechizo de ataque fuerte solo para "kk"\n'
    '-- (no para "k", que se usa contra cualquier mob).\n'
    'if clase and Clases[clase] and Clases[clase].defensa then\n'
    '  Clases[clase].defensa(obj)\n'
    'end\n\n'
    'Clases.despacharAtaque(obj)'
)

make_alias(
    clases_alias_group, "aa (ronda)", r"^aa(?: (\w+))?$",
    r'''-- "aa": un hechizo de ataque de Oteren por ronda de melee mientras estes en
-- combate. Medido en juego (diablo ingeniero): rayo ~350 (20 de mana),
-- ira/destruir ~235 (10 de mana); UN cast por ronda no le quita golpes al
-- melee (dos seguidos si).
--   aa                  carrusel: OFF -> JEFE -> AREA -> PVP -> OFF
--   aa on / off         prender o apagar (mantiene el modo elegido)
--   aa jefe|area|pvp    elegir modo y prender (tambien: rayo|ira|destruir)
-- JEFE = rayo de sinceridad (un objetivo, deslumbra); AREA = ira divina
-- (pega a todos los malignos de la sala); PVP = destruir maldad.
local modos = {
  {"JEFE", "rayo de sinceridad"},
  {"AREA", "ira divina"},
  {"PVP", "destruir maldad"},
}
local function indiceActual()
  for i, m in ipairs(modos) do
    if m[2] == Petria.rondaHechizo then return i end
  end
  return 0
end
local elegir = {jefe = 1, rayo = 1, area = 2, ira = 2, pvp = 3, destruir = 3}
local arg = (matches[2] or ""):lower()
if arg == "" then
  if not Petria.rondaActiva then
    Petria.rondaActiva = true
    Petria.rondaHechizo = modos[1][2]
  else
    local idx = indiceActual()
    if idx == 0 or idx >= #modos then
      Petria.rondaActiva = false
    else
      Petria.rondaHechizo = modos[idx + 1][2]
    end
  end
elseif arg == "limpiar" then
  Petria.noMalignos = {}
  Petria.inmunes = {}
  cecho("<cyan>aa: olvidados los mobs marcados como no malignos o inmunes\n")
  return
elseif arg == "on" then
  Petria.rondaActiva = true
elseif arg == "off" then
  Petria.rondaActiva = false
elseif elegir[arg] then
  Petria.rondaHechizo = modos[elegir[arg]][2]
  Petria.rondaActiva = true
else
  cecho("<red>Uso: aa [on|off|jefe|area|pvp]\n")
  return
end
local idx = indiceActual()
local etiqueta = Petria.rondaActiva and (idx > 0 and modos[idx][1] or "ON") or "OFF"
cecho(string.format("<cyan>Ronda: %s, hechizo: %s\n", etiqueta, Petria.rondaHechizo))'''
)

make_alias(
    clases_alias_group, "gpvp", r"^gpvp(?: (on|off))?$",
    r'''-- gpvp on|off: mandar golpetazo solo contra jugadores cuando estan medio bajos
-- de HP (no pueden tomar pociones). Sin argumento muestra el estado.
local arg = matches[2]
if arg == "on" then
  Petria.golpetazoPvP = true
elseif arg == "off" then
  Petria.golpetazoPvP = false
end
cecho(string.format("<cyan>golpetazo PvP: %s\n", Petria.golpetazoPvP ~= false and "ON" or "OFF"))'''
)

make_alias(
    clases_alias_group, "autocura", r"^autocura(?: (on|off))?$",
    r'''-- autocura on|off: curacion automatica por %HP en combate (75% -> 1 pocion,
-- 55% -> 2, 35% -> 3, con enfriamiento de 3 s). Sin argumento muestra el estado.
local arg = matches[2]
if arg == "on" then
  Petria.autoCurar = true
elseif arg == "off" then
  Petria.autoCurar = false
end
cecho(string.format("<cyan>Autocura: %s\n", Petria.autoCurar ~= false and "ON" or "OFF"))'''
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
    'Petria.huir()\n'
    'Petria.huir()\n'
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
    'Petria.traga("trans")\nPetria.traga("gris")\nPetria.traga("azul")\nPetria.traga("santuario")\n'
    'expandAlias("dope")\nexpandAlias("dope")\nexpandAlias("dope")'
)
make_alias(alias_group, "ihs", r"^ihs$", 'Petria.traga("gris")\nPetria.traga("trans")\nPetria.traga("santu")')
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
    '-- Confirmado en juego: mandar cada reintento a ciegas cada 0.7s (sin\n'
    '-- esperar la respuesta real del intento anterior) amontonaba pedidos\n'
    '-- en la cola de casteo del server -- seguian llegando "Hechizo\n'
    '-- fallado." (y hasta un exito tardio) DESPUES de que este alias ya\n'
    '-- habia dicho "Cancelacion fallida tras 6 intentos.", con mas mana\n'
    '-- gastado del que reflejaba el contador local. Ahora cada intento\n'
    '-- espera la respuesta real del server ("Hechizo fallado." dispara el\n'
    '-- siguiente intento) en vez de un timer ciego -- el timer de 4s queda\n'
    '-- solo como red de seguridad si el server no contesta nada.\n'
    '-- "Memoria corta" (Petria.canNadaHasta): confirmado en juego que en\n'
    '-- medio de una pelea tensa es facil reescribir "can <obj>" varias\n'
    '-- veces seguidas a mano sin darse cuenta que el intento anterior ya\n'
    '-- dijo "Nada que cancelar." -- cada llamada a este alias es\n'
    '-- independiente, no se acuerda de la anterior. Si el mismo objetivo\n'
    '-- dio "Nada que cancelar." hace menos de 8s, no vuelve a mandar el\n'
    '-- hechizo (evita gastar mana de nuevo en lo mismo).\n'
    'Petria.canNadaHasta = Petria.canNadaHasta or {}\n'
    'local tarjet = matches[2]\n'
    '-- Confirmado en juego: "can self" se quita TODOS tus buffs, el autodope los\n'
    '-- relanza, y como el mensaje de exito sobre uno mismo ("...se van\n'
    '-- despejando... Ok.") no es el de un objetivo ajeno, el alias lo tomaba por\n'
    '-- fallo y reintentaba 6 veces: cancelar y recastear en bucle (~900 de mana).\n'
    'local yo = gmcp and gmcp.Char and gmcp.Char.Base and gmcp.Char.Base.name\n'
    'local tl = tarjet:lower()\n'
    'if tl == "self" or tl == "yo" or (yo and tl == tostring(yo):lower()) then\n'
    '  cecho("<yellow>[can] no se usa sobre uno mismo: te quita todos los buffs y el autodope los relanza en bucle.\\n")\n'
    '  return\n'
    'end\n'
    'local tarjetKey = tarjet:lower()\n'
    'local vencimiento = Petria.canNadaHasta[tarjetKey]\n'
    'if vencimiento and os.time() < vencimiento then\n'
    '  cecho(string.format("<gray>[can] %s ya dijo \\"Nada que cancelar.\\" hace poco, no reintento.\\n", tarjet))\n'
    '  return\n'
    'end\n\n'
    'local intentos = 0\n'
    'local intentosMax = 6\n'
    'local terminado = false\n\n'
    'local function intentar()\n'
    '  intentos = intentos + 1\n'
    '  send("c \'cancelacion\' " .. tarjet)\n'
    '  local idExito, idNada, idFallo, idTimeout\n'
    '  local function limpiar()\n'
    '    if exists(idExito, "trigger") == 1 then killTrigger(idExito) end\n'
    '    if exists(idNada, "trigger") == 1 then killTrigger(idNada) end\n'
    '    if exists(idFallo, "trigger") == 1 then killTrigger(idFallo) end\n'
    '    if exists(idTimeout, "timer") == 1 then killTimer(idTimeout) end\n'
    '  end\n'
    '  -- Confirmado en juego (con codigo verificado, instalacion limpia sin\n'
    '  -- duplicados): igual salian los 6 intentos en rafaga. Sospecha: crear\n'
    '  -- un tempRegexTrigger nuevo con el MISMO patron ("Hechizo fallado.")\n'
    '  -- desde adentro del callback que esta procesando esa misma linea\n'
    '  -- puede hacer que Mudlet evalue el trigger recien creado contra la\n'
    '  -- linea que TODAVIA esta despachando, encadenando varios intentos en\n'
    '  -- el mismo tick. tempTimer(0.05, ...) saca la creacion del siguiente\n'
    '  -- intento de ese mismo ciclo de procesamiento.\n'
    '  local function siguienteOFinal()\n'
    '    limpiar()\n'
    '    if intentos < intentosMax then\n'
    '      tempTimer(0.05, intentar)\n'
    '    else\n'
    '      terminado = true\n'
    '      cecho(string.format("<red>Cancelacion fallida tras %d intentos.\\n", intentosMax))\n'
    '    end\n'
    '  end\n'
    '  -- Ademas de "se desvanece." (santuario), quitar acelerar da "X ya no va\n'
    '  -- a toda velocidad. Ok." (confirmado en juego): sin esto el alias lo\n'
    '  -- tomaba por fallo y reintentaba, gastando casts de mas.\n'
    '  idExito = tempRegexTrigger("(?:se desvanece|ya no va a toda velocidad)\\\\.", function()\n'
    '    if terminado then return end\n'
    '    terminado = true\n'
    '    limpiar()\n'
    '    cecho(string.format("<green>Cancelacion exitosa en %d intento(s).\\n", intentos))\n'
    '  end)\n'
    '  idNada = tempRegexTrigger("Nada que cancelar\\\\.", function()\n'
    '    if terminado then return end\n'
    '    terminado = true\n'
    '    limpiar()\n'
    '    Petria.canNadaHasta[tarjetKey] = os.time() + 8\n'
    '    cecho("<gray>Nada que cancelar en el objetivo.\\n")\n'
    '  end)\n'
    '  idFallo = tempRegexTrigger("Hechizo fallado\\\\.", function()\n'
    '    if terminado then return end\n'
    '    siguienteOFinal()\n'
    '  end)\n'
    '  idTimeout = tempTimer(4, function()\n'
    '    if not terminado then\n'
    '      siguienteOFinal()\n'
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

# "updatepkg" YA NO VIVE ACA. Vivia en este mismo paquete y se
# auto-desinstalaba con "uninstallPackage('Petria-Rhuna')" como parte de su
# propio reinstall -- si el installPackage() posterior fallaba (confirmado
# en juego, mas de una vez), no quedaba NINGUN "updatepkg" para reintentar,
# solo un paquete desinstalado y el usuario a ciegas. Se movio a un
# paquete separado y estable, "Petria-Rhuna-Updater" (ver el bloque al
# final de este script) que este paquete nunca toca ni desinstala -- se
# instala UNA sola vez y sobrevive a cualquier falla de reinstall de este.
make_alias(alias_group, "q", r"^q (.+)$", 'send("get " .. matches[2] .. " moch")\nsend("tra " .. matches[2])')

# Intercepta CUALQUIER "traga <obj>" -- tipeado a mano o mandado por
# nuestros propios triggers/teclas via send() (que dispara alias igual que
# texto tipeado, mismo patron ya usado en todo este paquete para llamar
# un alias desde otro). Bloquea si Petria.enZonaSinPociones() (Torre de la
# Desesperanza) en vez de dejar pasar el "traga" real, porque ahi
# teletransporta a un foso random -- mejor bloquear en un solo lugar que
# tener que acordarse de gatear cada tecla/trigger que usa "traga" por
# separado.
make_alias(
    alias_group, "traga", r"^traga (.+)$",
    '-- Guard de reentrada: si send() dispara este mismo alias de nuevo al\n'
    '-- reenviar el "traga" real (no confirmado si send() pasa por alias\n'
    '-- locales o no, pero mejor no confiarse), esto corta cualquier loop\n'
    '-- de entrada sin importar cual sea el comportamiento real.\n'
    'if Petria.enPasoTraga then return end\n'
    'if Petria.enZonaSinPociones() then\n'
    '  cecho("<red>[BLOQUEADO] \\"traga\\" te teletransporta a un foso en esta zona (Torre de la Desesperanza) -- usa un hechizo de cura en cambio.\\n")\n'
    '  return\n'
    'end\n'
    'Petria.enPasoTraga = true\n'
    'Petria.traga(matches[2])\n'
    'Petria.enPasoTraga = false',
)
make_alias(alias_group, "gp", r"^gp$", 'send("golpetazo")')

# Modo torneo: 10 pociones, 10 pergaminos, 10 varitas y 3 huidas.
make_alias(
    alias_group, "torON", r"(?i)^toron$",
    r'''Petria.torneo = true
Petria.huidas = 0
Petria.pocPend, Petria.varPend, Petria.huidasPend = 0, 0, 0
cecho("<green>[TORNEO] ACTIVADO: maximo 10 pociones, 10 pergaminos, 10 varitas y 3 huidas.\n")
expandAlias("tor")'''
)
make_alias(
    alias_group, "torOFF", r"(?i)^torOFF$",
    r'''Petria.torneo = false
cecho("<yellow>[TORNEO] DESACTIVADO: sin limites de pociones, varitas ni huidas.\n")'''
)
make_alias(
    alias_group, "tor (estado del torneo)", r"^tor$",
    r'''cecho(string.format(
  "<cyan>[TORNEO %s] pociones %d/10 | pergaminos %d/10 | varitas %d/10 | huidas %d/3\n",
  Petria.torneo and "ON" or "OFF",
  Petria.poc or 0, Petria.per or 0, Petria.var or 0, Petria.huidas or 0))'''
)
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
make_alias(
    alias_group, "za", r"^za$",
    '-- Cambiado de "puntero" (nivel 21, muy bajo) a "bendicion" (la varita\n'
    '-- de Don Puchito, hechizo sanar nivel 108). Confirmado en juego:\n'
    '-- "sos" (sostener) falla con "No puedes sostener un objeto mientras\n'
    '-- estes blandiendo dos armas." si ya estas dual-wield -- igual que la\n'
    '-- lanza de intentarEmpalar, hay que GUARDAR ambas armas ANTES de\n'
    '-- intentar sostener la varita, no alcanza con reequiparlas despues.\n'
    'if not Petria.usaVarita() then return end\n'
    'if Petria.armaValida(armaPrincipal) then send("gua " .. armaPrincipal) end\n'
    'if Petria.armaValida(armaSecundaria) then send("gua " .. armaSecundaria) end\n'
    'send("get bendicion moch")\n'
    'send("sos bendicion")\n'
    'send("zap self")\n'
    'if Petria.armaValida(armaPrincipal) then send("bla " .. armaPrincipal) end\n'
    'if Petria.armaValida(armaSecundaria) then send("segun " .. armaSecundaria) end',
)

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
    'Petria.huir("huir e"); Petria.huir("huir e"); Petria.huir("huir e")\n'
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

-- true si la raza del personaje conectado es gnomo (gmcp.Char.Base.race).
-- Usado por MonteGnomo: esa mecanica es racial, solo para gnomos -- igual
-- alcance que Clases.intentarAstucia (astucia gnoma), pero como esto no
-- es especifico de ninguna clase queda en Petria, no en Clases.
function Petria.esGnomo()
  return gmcp and gmcp.Char and gmcp.Char.Base and gmcp.Char.Base.race
    and gmcp.Char.Base.race:lower() == "gnomo"
end

-- true si la sala actual (gmcp.Room.Info.area) es "Torre de la Desesperanza".
-- Los 5 jefes de esa zona (Ferronox/Okskur/Kinkimo/Urtioica/Wendigo)
-- comparten un mobprog que dispara con la palabra "traga" en la sala (no
-- con "huir" como parecia a primera vista) y directamente TELETRANSPORTA
-- a quien la diga a un foso random -- tomar pociones/pildoras en esta
-- zona es literalmente peligroso, no solo inutil.
function Petria.enZonaSinPociones()
  return gmcp and gmcp.Room and gmcp.Room.Info and gmcp.Room.Info.area
    and gmcp.Room.Info.area:lower() == "torre de la desesperanza"
end

-- Cura HP: "traga sana" normalmente, pero en Petria.enZonaSinPociones()
-- eso te teletransporta a un foso (ver el mismo comentario en el alias
-- "traga"). Reemplazo con "la varita bendita de Don Puchito" (hechizo
-- sanar nivel 108 -- el "puntero" que usa el alias "za" es nivel 21,
-- muy bajo para nivel 90+). Esta varita esta justo en el 2do piso de la
-- Torre (sala #5805), se agarra de paso subiendo. Usa "zap", no "traga",
-- asi que no entra en el bloqueo. Usado por las teclas sanar/MAC-Sanar
-- en vez de repetir la logica en cada una.
-- true mientras tengas el efecto "golpetazo" (en "aff" sale como "Hechizo:
-- golpetazo ... Efecto: hinchado"; es lo que te deja sin pociones). Se lee de
-- gmcp.Char.Affects; de respaldo, el trigger "Golpetazo recibido" marca unos
-- segundos por si el afecto tarda en llegar.
function Petria.sinPociones()
  -- Lo mas exacto: la letra "G" (golpetazo) de %S en el prompt. La leen el
  -- trigger del prompt (cada linea), el mensaje "te hace ver las estrellas" y
  -- "!Bash!" (al recuperarte).
  if Petria.enGolpetazo ~= nil then
    return Petria.enGolpetazo
  end
  if Petria.golpetazoFinAt and os.time() - Petria.golpetazoFinAt < 3 then
    return false
  end
  if Clases and Clases.tieneActivo and Clases.tieneActivo("golpetazo") then
    return true
  end
  return Petria.sinPocionesHasta ~= nil and os.time() < Petria.sinPocionesHasta
end

-- Solo el Oteren tiene "sanar" entre las clases que uso; el Mago no puede
-- curarse de otra forma cuando le aplican golpetazo.
function Petria.puedeSanarConHechizo()
  local completa = gmcp and gmcp.Char and gmcp.Char.Base and gmcp.Char.Base.class
  return completa ~= nil and tostring(completa):lower():find("oteren", 1, true) ~= nil
end

function Petria.sanar()
  if Petria.sinPociones() and Petria.puedeSanarConHechizo() then
    send("c sanar")
    return
  end
  if Petria.enZonaSinPociones() then
    -- Modo torneo: sin varitas disponibles, un Oteren cae a "c sanar".
    if not Petria.usaVarita() then
      if Petria.puedeSanarConHechizo() then send("c sanar") end
      return
    end
    -- "sos" falla si ya estas dual-wield -- guardar ambas armas antes,
    -- no alcanza con reequiparlas despues (confirmado en juego).
    if Petria.armaValida(armaPrincipal) then send("gua " .. armaPrincipal) end
    if Petria.armaValida(armaSecundaria) then send("gua " .. armaSecundaria) end
    send("get bendicion moch")
    send("sos bendicion")
    send("zap self")
    if Petria.armaValida(armaPrincipal) then send("bla " .. armaPrincipal) end
    if Petria.armaValida(armaSecundaria) then send("segun " .. armaSecundaria) end
  else
    -- Modo torneo: sin pociones disponibles, un Oteren cae a "c sanar".
    if not Petria.traga("sana") and Petria.puedeSanarConHechizo() then
      send("c sanar")
    end
  end
end

-- "ronda": un cast por ronda de melee (ver alias "ronda" y trigger
-- "Ronda: lanzar hechizo" en Pelea).
if Petria.rondaActiva == nil then Petria.rondaActiva = false end
Petria.rondaHechizo = Petria.rondaHechizo or "rayo de sinceridad"

-- ================================================================
-- Modo torneo (torON / torOFF): limites de 10 pociones, 10 pergaminos, 10
-- varitas y 3 huidas. "Poc / Per / Var" del prompt son contadores de lo USADO
-- (no de lo que te queda). Todo el paquete toma pociones, usa varitas y huye
-- a traves de Petria.traga / Petria.usaVarita / Petria.huir para respetarlo.
-- "Pend" cuenta lo enviado que el prompt aun no refleja (rafagas).
-- ================================================================
if Petria.torneo == nil then Petria.torneo = false end
Petria.poc = Petria.poc or 0
Petria.per = Petria.per or 0
Petria.var = Petria.var or 0
Petria.huidas = Petria.huidas or 0
Petria.pocPend = 0
Petria.varPend = 0
Petria.huidasPend = 0

function Petria.restantes(usadas, pend, limite)
  if not Petria.torneo then return 999 end
  return math.max(0, limite - (usadas or 0) - (pend or 0))
end
function Petria.pocionesRestantes() return Petria.restantes(Petria.poc, Petria.pocPend, 10) end
function Petria.pergaminosRestantes() return Petria.restantes(Petria.per, 0, 10) end
function Petria.varitasRestantes() return Petria.restantes(Petria.var, Petria.varPend, 10) end
function Petria.huidasRestantes() return Petria.restantes(Petria.huidas, Petria.huidasPend, 3) end

function Petria.traga(obj)
  if Petria.pocionesRestantes() <= 0 then
    cecho("<red>[TORNEO] limite de 10 pociones alcanzado (Poc: " .. tostring(Petria.poc) .. "): no tomo '" .. tostring(obj) .. "'\\n")
    return false
  end
  Petria.pocPend = (Petria.pocPend or 0) + 1
  send("traga " .. obj)
  return true
end

function Petria.usaVarita()
  if Petria.varitasRestantes() <= 0 then
    cecho("<red>[TORNEO] limite de 10 varitas alcanzado (Var: " .. tostring(Petria.var) .. ")\\n")
    return false
  end
  Petria.varPend = (Petria.varPend or 0) + 1
  return true
end

function Petria.huir(cmd)
  if Petria.huidasRestantes() <= 0 then
    cecho("<red>[TORNEO] limite de 3 huidas alcanzado: omito '" .. tostring(cmd or "huir") .. "'\\n")
    return false
  end
  Petria.huidasPend = (Petria.huidasPend or 0) + 1
  send(cmd or "huir")
  return true
end

-- Palabra clave de un nombre de mob para comandos de una sola palabra
-- ("Una hormiga pretoriana" -> "hormiga"). Memoria de tipos "no malignos".
Petria.articulos = {{el = true, la = true, los = true, las = true, un = true, una = true}}
Petria.noMalignos = Petria.noMalignos or {{}}
Petria.inmunes = Petria.inmunes or {{}}
function Petria.palabraClave(nombre)
  for w in (nombre or ""):lower():gmatch("%S+") do
    if not Petria.articulos[w] and #w > 2 then return w end
  end
  return nil
end

-- true si "v" tiene un nombre de arma configurado. Confirmado en juego: gua /
-- bla / segun aceptan el nombre completo ("la Mandibula del fin de la Reina
-- Roja"), no hace falta una sola palabra.
function Petria.armaValida(v)
  return v ~= nil and v ~= ""
end

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

-- true si "nombre" esta en la lista de dope de la clase actual (substring en
-- ambos sentidos, igual que tieneActivo: "inspiracion" calza con
-- "inspiracion divina").
function Clases.enDope(nombre)
  local lista = clase and Clases.dopes[clase]
  if not lista then return false end
  local buscado = nombre:lower()
  for _, h in ipairs(lista) do
    local hl = tostring(h):lower()
    if hl:find(buscado, 1, true) or buscado:find(hl, 1, true) then
      return true
    end
  end
  return false
end

-- Recastea un buff que acaba de expirar, solo si esta en el dope de la clase.
-- No consulta GMCP a proposito: el mensaje de texto acaba de decir que se fue.
-- En combate solo se recastean los buffs clave de PvP: un disipar/cancelacion
-- saca 10 buffs juntos y cada cast cuesta una ronda (PvP contra Alien: ~700
-- de dano por ronda). Prioridad segun Sammer (PvP en Petria): vision
-- (gatovision, para que la cancelacion quite santuario/acelerar del rival),
-- santuario (reduce el dano a la mitad), acelerar (actua en defensa y en
-- ataque) y, en segundo orden, volar (evita la zancadilla). El resto
-- (bendecir, fuerza, protecciones, inspiracion...) queda para "dope".
Clases.buffsDeCombate = {
  gatovision = true, santuario = true, acelerar = true, volar = true,
}
function Clases.reponer(nombreDope, comando)
  if not Clases.enDope(nombreDope) then return end
  -- Confirmado en juego: un Oteren peleando recibe "No alcanzas la
  -- concentracion necesaria." al lanzar santuario (solo el Mago puede). Gasta
  -- un cast y mana para nada.
  if nombreDope == "santuario" and en_combate and en_combate ~= 0 then
    local completa = gmcp and gmcp.Char and gmcp.Char.Base and gmcp.Char.Base.class
    if completa and tostring(completa):lower():find("oteren", 1, true) then
      cecho("<yellow>En combate: Oteren no puede lanzar santuario, se omite.\\n")
      return
    end
  end
  if en_combate and en_combate ~= 0 and not Clases.buffsDeCombate[nombreDope] then
    cecho("<yellow>En combate: se omite recastear '" .. nombreDope .. "' (usa dope al terminar)\\n")
    return
  end
  send(comando)
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
  -- Confirmado en juego: sin armaPrincipal configurada, "bla lanza" suelta la
  -- principal por su cuenta y despues "bla " (vacio) da "Vestir, blandir o
  -- sostener que?" -- el resto de la pelea queda a punos. Sin saber que arma
  -- devolver, mejor no empalar y avisar.
  if not (Petria.armaValida(armaPrincipal)) then
    cecho("<yellow>[empalar] omitido: falta configurar tu arma con 'setarma <palabra>' (y 'setsegun <palabra>' si usas secundaria); si no, quedarias sin arma.\\n")
    return
  end
  send("gua " .. armaPrincipal)
  if Petria.armaValida(armaSecundaria) then
    send("gua " .. armaSecundaria)
  end
  send("get lanza moch")
  send("bla lanza")
  send("empalar " .. obj)
  send("gua lanza")
  send("bla " .. armaPrincipal)
  if Petria.armaValida(armaSecundaria) then
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
    Petria.traga("santu")
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
  -- Solo para "kk". Medido en juego contra un diablo ingeniero: "rayo de
  -- sinceridad" ~350 por cast (20 de mana) y ademas deslumbra al rival;
  -- "ira divina" y "destruir maldad" ~235 (10 de mana). Los tres solo dan a
  -- objetivos malignos. "ira divina" tiene area, por eso no se usa aqui.
  -- La clase GMCP "seguidores_de_Runk" tambien se reduce a "seguidores", asi
  -- que se chequea el nombre completo para no tirarlo con un Runk.
  defensa = function(obj)
    local completa = gmcp and gmcp.Char and gmcp.Char.Base and gmcp.Char.Base.class
    if not (completa and tostring(completa):lower():find("oteren", 1, true)) then
      return
    end
    if obj ~= "" and obj:lower() ~= "someone" then
      send("conjurar 'rayo de sinceridad' " .. obj)
    else
      send("conjurar 'rayo de sinceridad'")
    end
  end,
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
-- OJO: "Pelea" tiene que existir ANTES de definir cualquier Pelea.algo. Estaba
-- definida mas abajo: si la tabla no existia todavia, el script se caia en la
-- primera "function Pelea.alerta" y NADA de lo que sigue quedaba definido
-- (PeleaActualizarVitalsGMCP / PeleaActualizarEnemigoGMCP eran nil: sin
-- curacion automatica por HP, sin en_combate por GMCP, sin refrescar por mv).
Pelea = Pelea or {}

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

  -- Movimiento bajo EN COMBATE: pelear contra un enjambre (Reina Roja) gasta
  -- 20-35 de mv por ronda esquivando; al llegar a 0 dejo de esquivar y las
  -- mordidas pasaron de ~50-100 a ~180-260 por ronda (log en juego). Con mv
  -- en 0 el server no manda ningun mensaje, asi que el trigger de "demasiado
  -- cansado" nunca arranco. "c refrescar" confirmado en juego: +222 de mv.
  -- Solo clases con el hechizo (helpfile): Oteren y las listadas abajo.
  local mv, mvmax = tonumber(v.move), tonumber(v.maxmove)
  if mv and mvmax and mvmax > 0 and en_combate and en_combate ~= 0
     and mv < mvmax * 0.25 and (not cd_mv or cd_mv == 0) then
    local completa = gmcp.Char.Base and gmcp.Char.Base.class
    local nombre = completa and tostring(completa):lower() or ""
    local sinRefrescar = {seguidores_de_runk = true, druida = true, ladron = true}
    local mana = tonumber(v.mana)
    if nombre ~= "" and not sinRefrescar[nombre] and (not mana or mana >= 50) then
      send("c refrescar")
      cd_mv = 1
      tempTimer(3, function() cd_mv = 0 end)
    end
  end

  -- Curacion automatica por %HP (migrada de CMUD). Cambios respecto al
  -- original: solo EN COMBATE (no gastar pociones regenerando afuera), "traga
  -- sana" en vez de "traga sa" (el prefijo "sa" puede calzar con la pocion de
  -- santuario) y, en la Torre de la Desesperanza, Petria.sanar() -- ahi
  -- "traga" teletransporta al pozo. "autocura off" la apaga.
  if Petria.autoCurar ~= false and en_combate and en_combate ~= 0
     and (not curando or curando == 0) then
    local n = 0
    if HPpct < 35 then n = 3
    elseif HPpct < 55 then n = 2
    elseif HPpct < 75 then n = 1 end
    if n > 0 then
      if (Petria.enZonaSinPociones and Petria.enZonaSinPociones())
         or (Petria.sinPociones and Petria.sinPociones())
         or Petria.pocionesRestantes() <= 0 then
        Petria.sanar()
      else
        for _ = 1, n do Petria.traga("sana") end
      end
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

# Teclas numericas de la PC Linux, recreadas tras perderse en una limpieza
# total de paquetes. Codigos Qt estandar (NO capturados/confirmados como
# el resto de este archivo -- el usuario pidio explicitamente avanzar asi
# y corregirlos el mismo despues en el editor de Mudlet si no coinciden):
# "/" = 47, "*" = 42, "-" = 45, con el modificador de teclado numerico
# (igual que sanar/Savia verde, por las dudas sean especificas del
# numerico y no las mismas teclas del bloque principal).
QT_KEY_SLASH = 47
QT_KEY_ASTERISK = 42
QT_KEY_MINUS = 45

petria_key_group = make_key_group(key_pkg, "Petria-Rhuna")
teclas_key_group = make_key_group(petria_key_group, "Teclas")
make_key(teclas_key_group, "sanar", QT_KEY_INSERT, QT_KEYPAD_MODIFIER, "Petria.sanar()")
make_key(teclas_key_group, "recall", QT_KEY_END, 0, 'send("recall")\nsend("n")\nsend("curar")')
make_key(teclas_key_group, "Savia verde", QT_KEY_DELETE, QT_KEYPAD_MODIFIER, 'Petria.traga("savia")')
# Teclas Mac creadas a mano en la UI de Mudlet (leidas del perfil, codigos
# capturados). Reemplazan a MAC-Sanar / MAC-SaviaVerde, que usaban estos
# mismos codigos (123 / 125) y ya no existen en el perfil de la Mac.
make_key(teclas_key_group, "MAC-MejoraAlquimica", QT_KEY_BRACELEFT, 0, "send(\"c 'mejora alquimica' savia\")")
make_key(teclas_key_group, "MAC-SUPER", QT_KEY_BRACERIGHT, 0, 'Petria.traga("super")')
make_key(teclas_key_group, "MAC-Rayo", QT_KEY_MINUS, 0, 'if rasOBJ and rasOBJ ~= "" then send("c rayo " .. rasOBJ) end')
make_key(teclas_key_group, "Linux-MejoraAlquimica", QT_KEY_SLASH, QT_KEYPAD_MODIFIER, "send(\"c 'mejora alquimica' savia\")")
make_key(teclas_key_group, "Linux-Super", QT_KEY_ASTERISK, QT_KEYPAD_MODIFIER, 'Petria.traga("super")')
make_key(teclas_key_group, "Linux-Rayo", QT_KEY_MINUS, QT_KEYPAD_MODIFIER, 'if rasOBJ and rasOBJ ~= "" then send("c rayo " .. rasOBJ) end')
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

# ================================================================
# PAQUETE SEPARADO: Petria-Rhuna-Updater
# ================================================================
# Contiene SOLO el alias "updatepkg". Vive aparte de Petria-Rhuna a
# proposito: "updatepkg" hace uninstallPackage("Petria-Rhuna") +
# installPackage(...) -- si viviera adentro del mismo paquete que
# reinstala, se borraria a si mismo antes de terminar, y si el
# installPackage() posterior fallaba (confirmado en juego mas de una vez:
# fallos silenciosos de red / jsdelivr sin sincronizar todavia), no
# quedaba NINGUN "updatepkg" instalado para reintentar -- el usuario
# quedaba a ciegas con el paquete principal desinstalado y sin comando
# para recuperarlo, dependiendo de que alguien le pasara una URL manual.
# Este paquete updater es chico y estable (una sola funcion), no necesita
# actualizarse con la frecuencia del principal -- se instala UNA vez y
# sobrevive a cualquier falla de reinstall de Petria-Rhuna, porque
# updatepkg nunca desinstala/reinstala "Petria-Rhuna-Updater" (solo
# "Petria-Rhuna").
updater_root = ET.Element("MudletPackage", {"version": "1.001"})
ET.SubElement(updater_root, "TriggerPackage")
ET.SubElement(updater_root, "TimerPackage")
updater_alias_pkg = ET.SubElement(updater_root, "AliasPackage")
updater_alias_group = make_alias_group(updater_alias_pkg, "Petria-Rhuna-Updater")
ET.SubElement(updater_root, "ActionPackage")
ET.SubElement(updater_root, "ScriptPackage")
ET.SubElement(updater_root, "KeyPackage")
updater_var_pkg = ET.SubElement(updater_root, "VariablePackage")
ET.SubElement(updater_var_pkg, "HiddenVariables")

make_alias(
    updater_alias_group, "updatepkg", r"^updatepkg(?:\s+(-v|version))?$",
    '-- "updatepkg -v" (o "updatepkg version"): solo muestra el build de\n'
    '-- Petria-Rhuna instalado (Petria.version, definida alla, no aca) sin\n'
    '-- reinstalar nada. Si Petria-Rhuna no esta instalado (por eso este\n'
    '-- updater vive separado, ver nota abajo), Petria no existe todavia --\n'
    '-- se chequea con seguridad en vez de romper con un error de Lua.\n'
    'if matches[2] and matches[2] ~= "" then\n'
    '  if Petria and Petria.version then\n'
    '    cecho(string.format("<cyan>[Petria-Rhuna] Build instalado: %s\\n", tostring(Petria.version)))\n'
    '  else\n'
    '    cecho("<red>[Petria-Rhuna] No parece estar instalado (Petria.version no existe). Corre updatepkg para instalarlo.\\n")\n'
    '  end\n'
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
    '-- Instala desde GitHub (via raw.githack.com), no un archivo local:\n'
    '-- asi funciona igual en cualquier PC, no solo en la que genero el\n'
    '-- archivo. No usa raw.githubusercontent.com directo porque esa quedo\n'
    '-- bloqueada en la red corporativa de la Mac (confirmado con curl:\n'
    '-- "Connection reset by peer"). Se probo jsdelivr.net primero, pero\n'
    '-- confirmado en juego, repetidas veces, que jsdelivr podia tardar\n'
    '-- minutos en sincronizar un push nuevo incluso purgando su cache\n'
    '-- enseguida -- comparado en vivo con raw.githack.com/rawcdn.githack.com\n'
    '-- sobre el mismo push, esos dos ya mostraban el build nuevo mientras\n'
    '-- jsdelivr seguia atascado en el anterior. raw.githack.com (la\n'
    '-- variante pensada para contenido que cambia seguido, no la\n'
    '-- "produccion" rawcdn.githack.com) resulto mas confiable.\n'
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
    '    -- Confirmado en juego: el "DirectionKeyGroup" del GUI oficial\n'
    '    -- (numerico para movimiento, mismo modificador de teclado numerico\n'
    '    -- que usamos para sanar/Savia verde/Linux-Rayo/etc.) puede quedar\n'
    '    -- activo y pisar nuestras teclas custom con el mismo keyCode --\n'
    '    -- confirmado que producia resultados random (ej. "u" en vez de\n'
    '    -- lanzar rayo) hasta desactivarlo. Se desactiva solo en cada\n'
    '    -- update, sin que haga falta acordarse a mano. pcall porque puede\n'
    '    -- no existir si el GUI oficial no esta instalado.\n'
    '    pcall(disableKey, "DirectionKeyGroup")\n'
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

indent(updater_root)
updater_tree = ET.ElementTree(updater_root)
updater_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Petria-Rhuna-Updater.xml")

with open(updater_out_path, "wb") as f:
    f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE MudletPackage>\n')
    updater_tree.write(f, encoding="utf-8", xml_declaration=False)

print("OK ->", updater_out_path)
