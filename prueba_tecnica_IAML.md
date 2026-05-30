# [cite_start]PRUEBA TÉCNICA: SISTEMA RAG CON WEB SCRAPING [cite: 1]

* [cite_start]**Rol:** Machine Learning Engineer / AI Engineer [cite: 2]
* [cite_start]**Modalidad:** Individual, entrega en repositorio (GitHub, GitLab, Bitbucket o similar) [cite: 3]
* [cite_start]**Tiempo estimado:** 2 – 3 días [cite: 4]

---

## [cite_start]CONTEXTO [cite: 5]
[cite_start]BBVA Colombia necesita un asistente conversacional que permita a usuarios internos consultar información publicada en su sitio web institucional (https://www.bbva.com.co/), sin depender de búsquedas manuales. [cite: 6]

## [cite_start]¿QUÉ DEBES HACER? [cite: 7]
[cite_start]Un sistema RAG (Retrieval-Augmented Generation) en Python que tenga las siguientes funcionalidades: [cite: 8]

* Extraer información del sitio https://www.bbva.com.co/ mediante Web Scraping. (Puede ser de otro banco) [cite_start][cite: 9]
* [cite_start]Almacenar los datos scrapeados en local (Crudos y limpios). [cite: 10]
* [cite_start]Vectorizar e indexar ese contenido en una base de datos vectorial de tu elección. [cite: 11]
* [cite_start]Exponer una interfaz conversacional minimalista donde el usuario pueda hacer preguntas sobre el contenido del sitio. [cite: 12]
* [cite_start]Mantener el historial de conversación de acuerdo a un ID, teniendo en cuenta los N mensajes anteriores (N configurable). [cite: 13]

## [cite_start]REQUISITOS OBLIGATORIOS [cite: 14]

* **Lenguaje:** Python. [cite_start]El resto del stack es completamente libre. [cite: 15]
* **Dockerización:** El proyecto debe correr completamente con Docker. [cite_start]Se espera al menos un Dockerfile y un docker-compose.yml que levante todos los servicios necesarios si aplica (aplicación, base de datos vectorial, etc.) con un solo comando. [cite: 16]
* [cite_start]**Repositorio con historial:** El código debe estar en un repositorio público (GitHub, GitLab, Bitbucket o similar). [cite: 17]
  * [cite_start]Se evaluará el historial de commits: se espera ver una progresión lógica del trabajo, no un único commit con todo el código. [cite: 18]
  * [cite_start]Los mensajes de commit deben ser descriptivos. [cite: 19]
* [cite_start]**Patrones de diseño:** Implementa al menos 3 patrones de diseño (creacionales, estructurales o comportamentales). [cite: 20] [cite_start]Documentar cuáles se usó y por qué, en el README. [cite: 21]
* [cite_start]**Historial de conversación:** El sistema debe recordar el contexto de mensajes previos dentro de una sesión y persistir el historial de conversaciones. [cite: 22]
* [cite_start]**Interfaz:** Puede ser CLI, una UI web sencilla o un notebook interactivo. [cite: 23] [cite_start]Lo importante es que sea funcional y limpia, no que sea bonita. [cite: 24]
* [cite_start]**Herramientas sin costo preferidas:** Se valoran positivamente opciones como modelos open source, embeddings gratuitos y bases de datos vectoriales con tier gratuito o self-hosted. [cite: 25] [cite_start]El uso de APIs de pago es válido, pero no suma puntos adicionales. [cite: 26]
* [cite_start]**Análisis de datos:** Se debe incluir una funcionalidad que me permita recorrer el histórico de conversaciones para extraer métricas y valores de impacto. [cite: 27]
* [cite_start]**README:** El README debe permitir que cualquier persona pueda levantar y usar el sistema desde cero. [cite: 28] [cite_start]Como mínimo debería incluir: [cite: 29]
  * [cite_start]Requisitos previos (Docker, variables de entorno necesarias, etc.). [cite: 30]
  * [cite_start]Instrucciones paso a paso para clonar el repo, configurar el entorno y levantar el sistema con Docker. [cite: 31]
  * [cite_start]Cómo usar la interfaz conversacional una vez el sistema está corriendo. [cite: 32]
  * [cite_start]Patrones de diseño usados: cuáles son, dónde están aplicados y por qué se eligieron. [cite: 33]
  * [cite_start]Stack tecnológico elegido y justificación breve de cada decisión. [cite: 34]
  * [cite_start]Limitaciones conocidas o decisiones de diseño relevantes. [cite: 35]
  * [cite_start]Futuras mejoras del sistema. [cite: 36]

## [cite_start]BONUS (SUMA PUNTOS) [cite: 37]

* [cite_start]Implementación de un reranker para mejorar la relevancia de los resultados recuperados antes de pasarlos al LLM. [cite: 38]
* [cite_start]Manejo de errores. [cite: 39]
* [cite_start]Configuración externalizada (variables de entorno o archivo .env) para parámetros como N mensajes, modelo, chunk size, etc. [cite: 40]

## [cite_start]ENTREGABLES [cite: 41]

* [cite_start]**Repositorio** con el código fuente y el historial de commits visible. [cite: 42]
* [cite_start]**README** completo según lo descrito arriba. [cite: 43]

## [cite_start]FECHA DE ENTREGA [cite: 44]
[cite_start]A más tardar sábado 30 de mayo a las 11:59 PM. [cite: 44]

## [cite_start]Notas finales [cite: 45]

* No hay una única solución correcta. [cite_start]Se valora la capacidad de tomar decisiones técnicas razonadas y defenderlas. [cite: 46]
* Si tomaste un atajo o dejaste algo sin implementar, menciónalo en el README. [cite_start]La honestidad cuenta. [cite: 47]
* [cite_start]Ante cualquier ambigüedad en los requerimientos, documenta el supuesto que asumiste y sigue adelante. [cite: 48]