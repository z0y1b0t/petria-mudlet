# Petria-Mudlet — paquete único

Un solo paquete Mudlet (`Petria-Rhuna.xml`) con **una carpeta raíz
`Petria-Rhuna`** que va acumulando, como carpetas hermanas, todo lo migrado
desde CMUD:

```
Petria-Rhuna
├── Clases        ← hecho (incluye "dope" por clase)
├── Pelea         ← hecho (todo genérico por ahora, sin asociar a clase)
│   └── Autodope  ← hecho: recastea buffs propios al despejarse
├── Alias         ← hecho (resto de 18-Alias, salvo dd/ddo/ddq)
├── Oficios       ← pendiente
├── Quest         ← pendiente
├── Com           ← pendiente
├── ...
```

Cada categoría CMUD (`01-Oficios`, `03-Pelea`, `04-Quest`, `05-Com`, etc.) se
migra como una subcarpeta más de `Petria-Rhuna`, en los tres paneles de
Mudlet (Triggers, Aliases, Scripts) — no como archivos `.xml` sueltos. El
archivo `Petria-Rhuna.xml` se **reemplaza** en cada iteración de la
migración (se regenera completo), no se va parcheando a mano.

### ⚠️ Se renombró de "Petria" a "Petria-Rhuna" (una sola vez)

El server tiene un comando propio, `instalarmudlet`, que instala/actualiza
el paquete GUI **oficial** de Petria — y su propio texto de ayuda avisa
que "puede sobreescribir o eliminar configuraciones, triggers, alias y
scripts propios que tengas en un package Mudlet **con el mismo nombre**".
Nuestro paquete se llamaba literalmente `Petria`, un nombre genérico que
el instalador oficial fácilmente podría usar también — si coincidían,
correr `instalarmudlet` en el juego podía borrar todo este trabajo. Lo
renombré a `Petria-Rhuna` (carpeta raíz + nombre de archivo) para que no
tenga forma de chocar con nada oficial.

**Migración (una sola vez)**, porque el nombre del paquete cambió:
```
lua uninstallPackage("Petria")
```
```
lua installPackage("/home/rcaceres/Documentos/Claude/Projects/Petria-Mudlet/Petria-Rhuna.xml")
```
De ahí en más, `updatepkg` ya apunta solo al nombre nuevo. Nada de lo
guardado (`clase`, `Clases.dopes`, `petria_dopes.lua`, `armaPrincipal`
del GUI oficial, etc.) se pierde con el rename — son variables Lua y
archivos aparte, no dependen del nombre del paquete Mudlet.

## Disponible en las dos PCs: GitHub

Repo: **https://github.com/z0y1b0t/petria-mudlet** (público). Cada vez que
te mando una versión nueva, la subo ahí también. `updatepkg` ya instala
desde la URL raw de GitHub, no desde un archivo local — funciona igual sea
cual sea la PC donde lo corras, siempre que tengas internet.

Push con una **deploy key** dedicada a este repo (no tus credenciales
personales de GitHub, y solo con acceso a este repo puntual, no a toda tu
cuenta) — así que si en algún momento querés cortar el acceso, la borrás
desde `Settings → Deploy keys` del repo sin tocar nada más tuyo.

Para instalarlo por primera vez en la otra PC (con Mudlet + GMCP activado):
```
lua installPackage("https://raw.githubusercontent.com/z0y1b0t/petria-mudlet/main/Petria-Rhuna.xml")
```
Después, `updatepkg` funciona igual que en esta.

Fuente original: `/media/rcaceres/3B46BF9F7F346D5E/petria.xml` (export CMUD).

## GMCP disponible en este server

Confirmado con `lua display(gmcp)` en juego (mejor forma de descubrirlo: te
da todo lo que el server ya está mandando en ese momento). Lo que más sirve
para automatizar, en vez de parsear texto:

- `Char.Base`: `name`, `race`, `class`, `sexo`, `nivel`, `oficio`, `language`
- `Char.Vitals`: `hp`, `maxhp`, `mana`, `maxmana`, `move`, `maxmove`
- `Char.Stats`: `str`/`int`/`wis`/`dex`/`con` (+ `perm*`), `hitroll`,
  `damroll`, `spellpower`, `healpower`, `wimpy`
- `Char.Worth`: `money`, `xp`, `xptnl`, `maxxp`, `alignment`,
  `puntosquest`, `tiempoquest`, `practice`
- `Char.Enemies`: array con `{name, level, hp, maxhp, vnum}` del enemigo
  actual en combate
- `Char.Affects`: **`BuffYDebuff`** (hechizos activos: `name`, `duration`,
  `duration_type`), `vulnerable`/`resist`/`imm` (tipos de daño, como texto
  con códigos de color tipo `{Wlight{x`), `Equipamiento`, `Raciales`
- `Char.Grupo`: miembros del grupo con `name`, `class`, `level`, `hp`,
  `maxhp`, `mana`, `maxmana`, `mov`, `maxmov`, `leader`
- `Room.Info`: `name`, `area`, `vnum`, `exit` (direcciones disponibles)

Ya usamos `Char.Base` (detección de clase), `Char.Vitals`/`Char.Enemies`
(auto-heal y tracking de combate en `Pelea`) y `Char.Affects` (`dope`
inteligente y `cast00/01/02` en `ATAQUES`). `Char.Grupo` y `Room.Info`
quedan disponibles para cuando migremos algo que los necesite (por ejemplo
un radar de grupo, o navegación).

## `Petria/Clases`

Reemplaza el `#IF/#SWITCH` gigante de los alias `k` y `engancha` de CMUD por
una tabla Lua `Clases` con una subcarpeta de Script por clase de personaje.

- **Detección de clase**: se engancha al evento GMCP `gmcp.Char.Base` (lo
  mismo que ya usa el panel "Información del Personaje" del paquete
  `PetriaMUD_12.22.17`) y actualiza la variable global `clase` en tiempo
  real.
- **Aliases**: `k [objetivo]`, `engancha <objetivo>`, `panico`,
  `cguerrero`/`cmagos`/`cladron`/`cranger`/`cdruida`/`casesino`/`coteren`
  (recall — `coteren` es el de Seguidores, antes no estaba asociado a
  ninguna clase), y **`dope [objetivo]`** — ahora despacha directo a los
  hechizos de la clase conectada por GMCP, en vez del `dope` genérico de
  CMUD que llamaba a una función (`dope_continuar`) que nunca existió.
- **`dope` ahora es más inteligente que el original de CMUD**: al doparse a
  uno mismo, lee `gmcp.Char.Affects.BuffYDebuff` (hechizos activos, con
  duración) y **saltea los que ya están puestos** — esto era justo lo que
  `dope_continuar` iba a hacer en CMUD y nunca se implementó. A un objetivo
  (no uno mismo) tira la lista completa igual que antes, porque no podemos
  ver los afectos de otro personaje por GMCP.
- **`cast00`/`cast01`/`cast02`**: probé usar `gmcp.Char.Affects.vulnerable`
  para esto y estaba mal — ese campo es la vulnerabilidad del **personaje
  conectado** (cuelga de `gmcp.Char`, no de `gmcp.Char.Enemies`), no la del
  enemigo. GMCP no expone afectos del enemigo. Quedó como en CMUD: triggers
  de texto "vulnerable al Rayo/Fuego/acido." que setean
  `rayo_ok`/`fuego_ok`/`acido_ok`. `Clases.esVulnerableA` queda definida por
  si sirve para algo defensivo del propio personaje más adelante, pero no
  se usa en `cast00/01/02`.
- **Scripts**: `Clases_Core` (tabla base + helpers `Clases.dopar`,
  `Clases.tieneActivo`, `Clases.esVulnerableA`) + subcarpetas `Guerrero`,
  `Mago`, `Ladron`, `Ranger`, `Asesino`, `Druida`, `Seguidores`. Mago y
  Ranger tienen su lista de hechizos real de CMUD (`dopesmago`,
  `dopesranger`); Seguidores tiene `dopesoteren` armada a partir del
  comando `spells` en juego (autobuffs: acelerar, antifuego, bendecir,
  escudo luz, fuerza colosal, gatovision, luz protectora, protección
  infernal, protección sagrada, santuario, volar — sin curas puntuales ni
  detección/utilidad situacional). Guerrero/Ladron/Asesino/Druida no tenían
  lista de dope en
  CMUD, así que `dope` en esas clases avisa que no hay nada configurado.

## `Petria/Pelea`

Migración **literal** de `03-Pelea` (y sus 4 subclases CMUD ATAQUES/PK/WoF/
acoso) — a propósito **sin reclasificar por clase todavía** (eso viene
después, asociando cada trigger a su `Clases/<clase>` cuando confirmemos a
quién pertenece cada uno).

- **Triggers/Petria/Pelea**: ~33 triggers directos (cooldowns de hechizos,
  curación por sangrado, veneno, guardia del puente, etc.) + subcarpetas
  `ATAQUES`, `PK`, `WoF`, `acoso`.
- **Aliases/Petria/Pelea**: `skill <algo>` (guarda `ultima_skill` para
  reintentar) + subcarpeta `ATAQUES` con `cast00`/`cast01`/`cast02`.
- **Scripts/Petria/Pelea**: `Pelea_Core` — inicializa todas las variables
  globales (`en_combate`, `curando`, `cd_veneno`, `cd_guardia`, `qcomm`,
  `ultima_skill`, `rasOBJ`, `WoFriends`, flags de `ATAQUES`, etc.), define
  `ResetAliento()`, y engancha **auto-heal y tracking de enemigo por GMCP**:
  - `PeleaActualizarVitalsGMCP` (evento `gmcp.Char.Vitals`): cura por %HP
    (`HPcur`/`HPmax` reales, no texto parseado).
  - `PeleaActualizarEnemigoGMCP` (evento `gmcp.Char.Enemies`): setea
    `en_combate`, `enemigo_pct`, `enemigoNombre`, `enemigoNivel` con datos
    reales del server (antes era un trigger de texto con un patrón
    corrupto/desactualizado en el CMUD original, ya no se usa).

### Nuevo: `Petria/Pelea/Autodope`

Recastea buffs propios apenas se despejan, asociado a mano contra tu lista
de `spells` (seguidores_de_Oteren) y los mensajes de "se te pasa el
efecto":

| Mensaje | Recastea |
|---|---|
| Los efectos de Santuario se van despejando. | `santuario` |
| Sientes como tu inspiracion divina te abandona... | `inspiracion divina` |
| Te sientes mas debil. | `fuerza colosal` |
| Tu proteccion contra el mal mengua. | `proteccion infernal` |
| El escudo de luz que te rodeaba desaparece. | `escudo luz` |
| Los rayos de luz que te rodeaban desaparecen. | `luz protectora` |
| Tu proteccion sagrada se desvanece | `proteccion sagrada` |
| Ya vuelves a recuperar tu ritmo normal. | `acelerar` |
| Despacito dejas de levitar como un Lama tibetano. | `volar` |
| La bendicion ya no tiene efecto. | `bendecir` |

**No asociado**: "Comienzas a descongelarte." — no matchea con ningún
hechizo de tu lista de spells; podría ser el fin de un efecto hostil
(maldición), no un buff propio. Confirmar antes de agregarlo.

**"Te sientes menos cansado."** — al final SÍ es intencional repetir: es la
confirmación de que el curandero curó un poco de `move` (ej. "[+180
move]"), y hay que seguir pidiendo cura hasta llenarlo. El trigger chequea
`gmcp.Char.Vitals.move` vs `maxmove` y solo repite `curar refre` si todavía
no está lleno. Primer intento no disparó: el patrón tenía un `$` (fin de
línea) pegado justo después de "cansado.", pero la línea real sigue con
"[+180 move]" — nunca podía matchear. Sacado el anchor.

### Nuevo: protecciones contra ataque de jugador (PK)

Análisis de un log real donde te atacó otro jugador y casi no pudiste
reaccionar — encontré 3 problemas concretos y los protegí:

- **Alerta + reacción automática ante algo no identificado**: `Someone`
  aparece cuando no podés ver/detectar a quien te ataca (no es exclusivo de
  PK) — pero confirmado en juego que sirve como objetivo real para comandos
  de ataque (tus propios golpes también se describen como "a Someone").
  Apenas "Someone empieza a atacarte": banner visual fuerte + `k Someone`
  (contraataque con la clase conectada). **Saqué el `can Someone`**
  (cancelación) que había agregado antes — si "Someone" no es un target
  válido para ese hechizo específico, puede no encontrar objetivo y terminar
  cancelando tus propios buffs, peor que no cancelar nada. Si me confirmás
  la sintaxis correcta para cancelar a alguien no identificado, lo agrego
  bien.
- **Consejo de Santana** ("si ya inició la pelea recupera santuario y
  volar"): ahora la misma alerta de "Someone" recasta `santuario`/`volar`
  si `Char.Affects.BuffYDebuff` dice que no los tenés activos — confirmado
  en el log anterior que ambos se pueden despejar en medio de un PK real.
- **Alerta de Vigía de clan**: los vigías avisan cuando un enemigo entra a
  un área (`[Alerta](Vigia Explorador) Arikel --> detecta presencia
  enemiga: Alien en El Olimpo`). Si el área coincide con
  `gmcp.Room.Info.area` (tu área actual — confirmado que existe con `lua
  display(gmcp)`), banner de alerta + corre `rango` automático para ver
  quién anda cerca de verdad.
- **Recall bloqueado en zonas (NO RECALL)**: confirmado en el log, quedaste
  reintentando `recall` cientos de veces en una zona donde nunca iba a
  funcionar ("Los Dioses te han olvidado." cada vez). Ahora ese mensaje
  activa un flag `recallBloqueado` (15 seg) que corta los reintentos
  automáticos y avisa para que te muevas a mano.
- **Garganta degollada**: confirmado que tomar una poción con la garganta
  cortada **empeora la herida** ("tu garganta degollada se abre causando X
  heridas mas") — el auto-heal seguía intentando `traga sa` igual. Ahora un
  flag `gargantaCortada` (20 seg) pausa el auto-heal por poción durante ese
  tiempo y alerta para curar de otra forma.

`Pelea.alerta(mensaje)` (en `Pelea_Core`) es el banner reutilizable —
por ahora solo visual (texto grande en rojo/amarillo), sin sonido. Mudlet
soporta `playSoundFile(ruta)` si en algún momento querés sumar un audio de
alarma; avisame y lo agrego.

### Validado contra un combate real (mago vs "el Destructor")

Analizando un log real: `k`, las 3 debilidades (rayo/ácida + su recast al
vencer), y el post-kill funcionan exactamente como se diseñaron. Encontré y
arreglé dos problemas reales que aparecieron en ese mismo log:

- **Re-equipar tras desarme**: el mensaje `[DESARME] El objeto desarmado no
  coincide` que salió en el log **no era de este paquete** — ya existe un
  sistema completo para esto en `PetriaMUD_12.22.17` (el GUI, instalado
  aparte): alias `setarma <palabra>` / `setsegun <palabra>` que guardan el
  arma principal/secundaria en `estado_gui.lua`, más su propio trigger de
  recuperación. El mensaje salió porque esas variables todavía no estaban
  configuradas. **Saqué mi trigger de "Pelea"** que hacía lo mismo (hubiera
  duplicado el re-equipar en cada desarme) — corré `setarma <palabra clave
  de tu arma principal>` y `setsegun <palabra clave de la secundaria>` una
  vez y listo.
- **WoF/PK disparaban en combate PvE normal**: patrones como "han sido
  cegados por la suciedad!" y "esta aqui!" existen tanto en `Pelea` (PvE)
  como en `WoF`/`PK`. Confirmado en juego: al cegar a un enemigo normal, el
  trigger de `Pelea` mandaba `zancadilla` (correcto) PERO el de `WoF`
  **también** disparaba `huir` x3 al mismo tiempo — perdiste un combate que
  estabas ganando. `disableTriggerGroup("WoF")` (que `k` ya llamaba) no
  alcanzaba para evitarlo. Ahora `WoF` y `PK` están **apagados por defecto**
  con un flag explícito (`wofActivo`/`pkActivo`, chequeado al principio de
  cada uno de sus triggers) — activalos solo cuando estés realmente en ese
  modo:
  ```
  wof on   /   wof off
  pk on    /   pk off
  ```
  `panico` los apaga a los dos automáticamente.
- **3 prompts fantasma tras matar** ("Invocar el hechizo ¿sobre quién?"):
  los `tempTimer` de recast de `aliento tormentoso`/`golpe acido`/`rayo
  poderoso` quedaban corriendo y podían dispararse justo en la ventana de
  carrera al terminar el combate. Ahora se cancelan explícitamente
  (`Pelea.cancelarTimersPendientes()`) apenas termina el combate (por texto
  o por GMCP), en vez de confiar solo en el chequeo de `en_combate` dentro
  del timer.

### Nuevo: `addspell` / `removespell` (persisten entre reinstalaciones)

Para no tener que pedirme un reinstall cada vez que subís de nivel y
aprendés un hechizo nuevo:

```
addspell <hechizo>      -- lo agrega al dope de la clase conectada
removespell <hechizo>   -- lo saca
```

Las listas de dope ahora viven en `Clases.dopes[clase]` (antes eran
variables sueltas `dopesmago`/`dopesranger`/`dopesoteren`) y se guardan en
`<carpeta de Mudlet>/petria_dopes.lua` con `table.save`. Al reinstalar el
paquete, `Clases_Core` carga ese archivo **antes** de que cada clase
declare su lista de fábrica (`Clases.dopes.mago = Clases.dopes.mago or
{...}`), así que lo guardado tiene prioridad y sobrevive. Ahora **todas**
las clases (incluidas Guerrero/Ladrón/Asesino/Druida, que no tenían lista
en CMUD) tienen una función `dope` que arranca vacía y se llena con
`addspell`.

### Fix importante: el comando de curar era "q", tenía que ser "traga"

CMUD usaba `q <objeto>` (ej. `q sa`, `q ceguera`, `q santu`) para consumir
pociones/píldoras curativas. Confirmado en juego: `q sana` devuelve "Nada."
— el comando correcto es **`traga <objeto>`**. Afectaba 9 lugares distintos
(18 apariciones), incluido **el auto-heal de `Pelea`** (`traga sa` ahora en
vez de `q sa`) — probablemente no estaba curando nunca. Ya corregido en
todos lados.

### Fix importante: los paths con "." de CMUD gritan en vez de caminar

CMUD usa notación compacta (`.4sw`, `.3sw2swse`, etc.) para caminos rápidos.
**En este server/Mudlet, cualquier mensaje que empieza con "." se interpreta
como GRITAR**, no como camino — confirmado en juego (`.feo .` → `Gritas
'feo .'`). Afectaba a: `donas`, `bc`, `pocionesfull`, `saciar`, `limo`,
`arena`, `banco`, `pocsantu`, `cambio`, `pociones`, y los recall de
`Asesino` y `Seguidores` — **10 alias en total**, todos con el mismo bug.

Se reescribieron todos como secuencias explícitas de pasos cardinales
(`n`/`s`/`e`/`w`, confirmados válidos en juego). Las diagonales originales
(ej. "sw" en ".4sw") se descompusieron en 2 pasos cardinales en vez de un
solo comando diagonal — aunque confirmaste que `ne` funciona como paso
único, no quise apostar a si es `sw` (inglés) o `so` (español, como se ve
en el prefijo de salidas `NE NO SE SO`) para suroeste/noroeste, así que
usé la forma 100% segura ya confirmada (n/s/e/w sueltos).

### Nuevo: agarrar objetos "(LEGENDARIO)" del cadáver

Trigger "Objeto legendario en cadáver": cuando aparece una línea que empieza
con `(LEGENDARIO)` en el contenido del cadáver (se ve con `lo`/`exam cu`,
que el post-kill ya dispara).

Probé dos apuestas simples que **no funcionaron** (confirmado en juego):
`coger legendario` y `coger legendari` (por si el matcheo era por prefijo).
`(LEGENDARIO)` es solo una etiqueta de rareza, no una palabra clave — y con
"cientos" de objetos distintos no hay una sola palabra fija que sirva
siempre.

Solución actual: se saca el texto entre paréntesis (todas las etiquetas) de
la línea, y se usa la **primera palabra significativa** del nombre que
queda (saltando artículos como "un/una/el/la/los/las/de/del") como palabra
clave. Ejemplo: `(LEGENDARIO) (Magico) una Calabaza Legendaria` →
`coger calabaza`.

Es una heurística, no una certeza — el juego podría indexar otra palabra
del nombre como keyword real. Probá con varios objetos legendarios
distintos y avisame cuáles fallan para ajustar la lógica (por ejemplo, si
siempre falla con la primera palabra pero funciona con la última, cambio el
criterio).

### ⚠️ Revisar antes de confiar en esto en combate real

- Igual que con cualquier automatización: **probá primero en un lugar
  seguro** antes de confiar en que el auto-heal te salve la vida.
- **No migrado**: un trigger de CMUD con patrón
  `{un|unos}(%1) * cercano, al  (%w).` (prioridad 23781). La sintaxis
  `(%1)` dentro del propio patrón no es un wildcard estándar de CMUD y no
  lo pude traducir con confianza. Si sabés qué hace, decime y lo migro.
- **`cast02`** usa la variable `ataque02`, que no estaba definida en el
  CMUD original (solo existían `ataque00 = "golpe"` y
  `ataque01 = "aliento tormentoso"`). Queda vacía hasta que me digas qué
  hechizo va ahí.
- **`acoso`**: en CMUD cada patrón tenía `@acosado` interpolado directo en
  el texto (dinámico). Mudlet no soporta patrones dinámicos así, lo
  reescribí como un único trigger que matchea cualquier línea y filtra en
  Lua si contiene el nombre actual de `acosado` — funcionalmente
  equivalente, pero es la parte más reescrita (no migración línea a línea).
- Todas las funciones que en CMUD eran otros alias (`skill golpeta`,
  `skill zancadilla`, `skill corte_artero`, `skill rodear`, `skill furia`,
  `skill coce`, `skill astucia`) se invocan con `expandAlias(...)`, que
  ejecuta el comando como si lo hubieras tecleado — necesitan que el alias
  `skill` (ya migrado) esté activo.
- Validé mecánicamente los 88 bloques de Lua (llaves/paréntesis/bloques
  balanceados) y los 80 patrones regex (compilan) — pero es una
  verificación estructural, no funcional. Probar en juego sigue siendo
  necesario.

## `Petria/Alias`

Migración del resto de `18-Alias` de CMUD (65 alias en total ahí, menos
`k`/`cguerrero`/`cmagos`/`cladron`/`cranger`/`cdruida`/`casesino` que ya
viven en `Clases`, y menos `dd`/`ddo`/`ddq` que quedan para cuando migremos
`DD-Engine` completo — son parte de ese motor de farming, no alias sueltos).

Incluye compras/banco (`banco`, `pocionesfull`, `pocsantu`, `pociones`,
`limo`, `saciar`, `arena`), hechizos de un solo comando (`mm`, `rp`, `fuen`,
`alqui`, `portal`, `toso`, `ttortu`, `tbuho`, `canimal`, `des`, `mal`,
`rai`, `encantar`), macros de recall/movimiento (`donas`, `pan`, `bc`,
`reca`, `fabada`), gestión de `WoFriends` (`ene add/del`), y `can`
(cancelación con reintento, detecta éxito por texto del server).

- **`Petria_Core`** (Scripts, directo bajo `Petria`, no dentro de una
  subcarpeta): agrega `Petria.esperarTexto(patron, callback, timeoutSeg)`,
  el reemplazo de `#waitfor`/`#wait` de CMUD (no existen en Mudlet) — crea
  un trigger temporal que se autoelimina al matchear o al vencer el
  timeout.
- Los `#T+`/`#T-` a carpetas que todavía no migramos (`11-EQ`) quedan
  envueltos en `pcall` para no romper nada.
- Las funciones que en CMUD eran otro alias (`skill golpeta`, etc., y ahora
  también `can`) se invocan con `expandAlias(...)`.

## Actualizar de ahora en más: `updatepkg`

Alias que hace el uninstall + reinstall en un solo comando (con un delay
corto entre medio, porque encadenarlos en una sola línea de `lua` daba
"package X is already installed" por timing):

```
updatepkg
```

**Ojo**: esto recién existe DESPUÉS de instalar esta versión del paquete al
menos una vez de la forma manual de siempre. De ahí en más, cualquier
`Petria-Rhuna.xml` nuevo que te mande se instala con `updatepkg` en vez de
los dos comandos `lua`.

## Instalar / probar

1. Recomendado: probar primero en el perfil **PetriaDEV**, no en Petria (el
   perfil "productivo").
2. Reinstalar (uninstall + install, si ya lo tenías instalado de antes con
   el nombre viejo "Petria", ver la sección de arriba sobre el rename):
   ```
   lua uninstallPackage("Petria-Rhuna"); installPackage("/home/rcaceres/Documentos/Claude/Projects/Petria-Mudlet/Petria-Rhuna.xml")
   ```
3. La variable `clase` se llena sola en cuanto el server manda GMCP
   `Char.Base`. Para forzarla a mano: `lua clase = "guerrero"`.
4. Probar `k <blanco>`, `engancha <blanco>`, `panico`, los recall
   `c<clase>`, y — con cuidado — dejar que el auto-heal actúe una vez en un
   lugar seguro para confirmar que cura bien.

## Siguiente

Migrar como próxima subcarpeta de `Petria`: `01-Oficios`. Después:
`02-Habituales`, `04-Quest`, `05-Com` (DISCORD/COMM/CLAN/COMM_FMT),
`08-Rastrear`, `12-Puertas`, `13-Logs`, `17-Variables`, `19-Desarmar`,
`20-Misc`, `CAN`, `DD-Engine` (con `dd`/`ddo`/`ddq`), `Entrenar`,
`Equipaje`, `MonteGnomo`, `UTF8`. Y, cuando confirmes cada caso, ir
asociando triggers de `Pelea` a su `Clases/<clase>` correspondiente.
