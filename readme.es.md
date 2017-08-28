# Python news parser for dictionary attacks

Esta herramienta parsea noticias y guarda las palabras y cantidad de apariciones en una base de datos. Hace uso de un analizador sintáctico (**Part of Speech Tagger**) y un reconocedor de entidades (**Named Entity Recognizer**) para crear listados que se puedan usar en ataques de diccionario.

La herramienta parsea noticias de sitios de Argentina y hace uso de Natural Language Processing con modelos en español. Sin embargo, es sencillo agregar modelos para otros idiomas, así como también código para otros sitios de noticias.

*Leer en otros idiomas: [English](readme.md)*

### Justificación
 - Las palabras son actuales y específicas de un lugar. Los diarios de Argentina producirán palabras relevantes para Argentina.
 - Además, habrá palabras de celebridades, empresas y demás objetos de la cultura actual, a nivel local y mundial.

## Uso

```bash
$ python2 news_parser.py
```

## Natural Language Processing

No todas las palabras en una noticia son almacenadas. La elección de las palabras se hace mediante el uso de 2 herramientas hechas por **The Stanford Natural Language Processing Group**. Estas herramientas no se incluyen aquí, pero sí el enlace de donde pueden ser descargadas. También incluyo los scripts de bash que llaman a estas herramientas.

### Stanford Log-linear Part-Of-Speech Tagger

Esta es una tool hecha en Java que analiza sintácticamente las oraciones, identificando sus componentes. Del análisis vamos a conservar sustantivos y adjetivos para los diccionarios, descartando otras palabras como verbos, artículos, etc.

El modelo utilizado es en español y se puede descargar también del sitio de Stanford NLP Group. Además, es posible entrenar y utilizar tu propio modelo si así lo deseas.

**Sitio:** https://nlp.stanford.edu/software/tagger.html

### Stanford Named Entity Recognizer

Otra herramienta en Java que etiqueta palabras en una oración, detectando aquellas que son nombres, lugares y organizaciones. Nuevamente, se usó un modelo en español que se ofrece en el sitio del grupo, pero puede ser cambiado.

**Site:** https://nlp.stanford.edu/software/CRF-NER.html

## Dependencias

 - Python 2.7
 - Java 1.8+
 - [Stanford POS Tagger](https://nlp.stanford.edu/software/tagger.html)
 - [Stanford Named Entity Recognizer](https://nlp.stanford.edu/software/CRF-NER.html)
 - MongoDB y PyMongo
 - Beautiful Soup 4
 - Selenium WebDriver para Python
 - [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/) (o cualquier otro navegador que prefieras)

## Parseando las noticias

Para algunos sitios de noticias, su código fuente puede obtenerse de una sola vez (Infobae, Página 12, etc), mientras que otros sitios **generan el html de forma dinámica** (Clarín, Olé, etc). Para estos últimos, he utilizado un **Web Driver** que automáticamente abre y **navega los sitios hasta el final**, logrando que todo el contenido sea cargado en la página.

Para agregar nuevos sitios es necesario:

### 1- Agregar una función que procese la portada y recupere los enlaces a las noticias
Esta rutina debe recibir la url como argumento y retornar un set de urls.

Para el sitio de Infobae se ha utilizado urllib para obtener el código fuente, que luego es manipulado con Beautiful Soup para obtener todos los href:

![urllib](http://i.imgur.com/PmYS6hF.png)

En el caso de Clarín el contenido se carga dinámicamente, por lo que he usado Selenium para obtener el html, que luego se pasa a Beautiful Soup:

![selenium](http://i.imgur.com/Yc2mvrJ.png)

### 2- Modificar *get_news_hrefs_from_main_page()* para que incluya el nuevo sitio
![get_news_hrefs_from_main_page](http://i.imgur.com/fcULMQk.png)

### 3- Agregar la url de la portada en la función *main()*
![main](http://i.imgur.com/br0Sfwo.png)

### 4- Agregar la rutina que parsea las noticias individuales
Esta función recibe la url de la noticia y devuelve un buffer con el texto. Este es parte del código para Infobae:

![Parse news site](http://i.imgur.com/joTMXc0.png)

### 5- Modificar *get_news_text()* para incluir el nuevo sitio

## Base de Datos

La información se almacena en una MongoDB. Cada sitio de noticias tiene su propia base de datos, con las siguientes colecciones:

 - **words_all**: sustantivos y adjetivos en todo el texto de la noticia (título + subtítulo + cuerpo). Es el resultado de aplicar PoS Tagger a la noticia. Ejemplo:
 
`{'word' : 'obama', 'count' : 174}`

 - **words_names**: nombres, lugares y organizaciones en todo el texto de la noticia. Es el resultado de aplicar NER.

 - **words_headlines**: sustantivos y adjetivos que se encuentran solamente en el título de la noticia. La noticia en sí es ignorada.

 - **words_names_hdl**: nombres, lugares y organizaciones en el título.

 - **urls**: todas las urls que ya se procesaron. Ejemplo:
 
`{'url' : 'http://www.infobae.com/politica/2017/08/25/causa-hotesur-el-juez-ercolini-cito-a-indagatoria-a-cristina-kirchner/'}`

 - **logs**: cantidad de palabras y urls que han sido agregadas a la BD en una ejecución específica.
 
`{'words_all' : 5990, 'words_names' : 1451, 'words_headlines' : 429, 'words_names_hdl' : 126, 'urls' : 83, 'date' : datetime.datetime(2017, 8, 15, 16, 49, 18, 87000)}`

## Periodicidad de ejecución y procesos que se cuelgan

Vas a encontrar un archivo de crones (crontab) en el directorio principal. En mi caso, yo ejecuto el parser cada 6 horas, pero esto puede ser cambiado de ser necesario.

A veces los procesos de Java de las herramientas de Stanford (NER y PoS Tagger) se cuelgan y nunca terminan, deteniendo toda la ejecución. En lugar de analizar cuál es la causa, simplemente creé un script en bash que busca procesos de Java que se estén ejecutando por más de 5 minutos y los mata. Esto significa que esa noticia no termina de ser procesada y la ejecución continúa con la siguiente noticia.

El script es ***hippie_killer.sh*** y también es llamado desde ***.crontab***.

## Cantidad de palabras nuevas en el tiempo

El siguiente gráfico muestra el número de palabras nuevas por cada semana de ejecución, para el sitio de Infobae. Estos datos corresponden a la colección ***words_all***.

![nuevas palabras](http://i.imgur.com/mivC7V8.png)

## Diccionarios

Si no te interesa el código y solamente viniste por los diccionarios, los encontrarás en la carpeta **dict**.

Hay que tener en cuenta que estos diccionarios son solamente el punto de partida. Es necesario entender cómo combinar las palabras, generar máscaras adecuadas o combinar con reglas para que los diccionarios tengan algún éxito.

Se agregarán más diccionarios a medida que haya nuevo código para manejar otros sitios de noticias.

## Ideas y sugerencias

No voy a desarrollar código para otros sitios nuevos, por lo que espero **tu colaboración** y la de todos los que usen la herramienta para agregar nuevos sitios.

No solamente puedes aportar código, sino también ideas, sugerencias y diccionarios. Aquí algunas ideas:

 - Sería interesante almacenar en la BD si una palabra es un nombre de persona, o un lugar, o una organización. De esta forma, se puede armar diccionarios específicos de nombres, por ejemplo. Es muy común ver contraseñas como 'nombre' + 'teamo' en español.

 - Lo mismo, pero con un diccionario para sustantivos, otro para adjetivos, etc. Así, se haría más fácil unir palabras para formar combinaciones válidas.
