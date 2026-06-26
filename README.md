# Investor Scout (MVP) 🚀
Una plataforma de inteligencia para inversores de valor (*Value Investing*) que automatiza el trabajo más difícil: analizar empresas leyendo documentos oficiales (10-K, 10-Q), calcular su valor intrínseco, generar tesis de inversión y monitorear el portafolio automáticamente.

---

## 🏗️ Arquitectura y Entidades Base
Basado en principios limpios de ingeniería, los datos de los activos se separaron en dos perspectivas:
* **`Company`**: Datos estáticos y cualitativos (Ticker, Sector, Moat, Modelo de Negocio).
* **`FinancialSnapshot`**: Historial de la salud financiera por trimestre (Precio, ROE, Deuda, Márgenes).

Otras entidades creadas: `User`, `Portfolio`, `Holding` (Calculado dinámicamente) e `InvestmentThesis` (AI Generated).

---

## ✅ Etapa 1: Estructuras de Datos Puras (COMPLETADO)
Para la Fase 1, evitamos el uso de bases de datos (MySQL) para construir y comprender cimientos puros en memoria usando Python. Se construyeron 4 estructuras de datos críticas en `app/data_structures/`:

### 1. Historial Inmutable (`TransactionLinkedList`)
Una **Lista Enlazada (Linked List)** que actúa como un log de transacciones (`BUY`, `SELL`) que nunca se borran ni modifican. Los "Holdings" activos del portafolio se calculan matemáticamente reproduciendo esta historia de principio a fin, asegurando que el costo promedio y ganancias realizadas sean perfectas.

### 2. Cache de Precios (`StockCache`)
Una **Tabla Hash (Diccionario Python)** que permite consultas de lectura `O(1)`. Está integrado con la API de `yfinance` para traer precios reales y guardarlos en memoria, evitando quemar la API con peticiones repetitivas. Incluye funcionalidad de `force_refresh`.

### 3. Jerarquía Financiera (`PortfolioTree`)
Un **Árbol Polimórfico** (`raíz -> sectores -> empresas`) donde el principio básico es la recursividad. Si le preguntas al Portafolio (raíz) cuánto vale, este suma su efectivo (Cash) y le pregunta a sus ramas (Sectores) cuánto valen. Los sectores le preguntan a las hojas (Empresas), haciendo los cálculos limpios y escalables.

### 4. Detección de Riesgos en Cascada (`CompanyRelationshipGraph`)
Un **Grafo de Listas de Adyacencia** diseñado para conectar empresas mediante aristas (relaciones): `SUPPLIER`, `CUSTOMER`, `COMPETITOR`. Si una empresa global (Ej. TSMC) sufre una crisis, el grafo es capaz de escanear el portafolio y avisar qué acciones están expuestas al riesgo.

---

## 🔄 Estado Actual (Pruebas en `main.py`)
En la raíz del proyecto existe un archivo `main.py` que actualmente ejecuta con éxito la simulación de toda la arquitectura anterior:
1. Crea un usuario y un portafolio.
2. Compra y vende acciones de AAPL y NVDA, y calcula los *Holdings* mediante la LinkedList.
3. Prueba el Hash Table haciendo descargas en tiempo real con `yfinance`.
4. Evalúa un portafolio de $12,300 de forma recursiva con el Árbol.
5. Inyecta una noticia mala simulada a `TSM` y el Grafo detecta automáticamente los riesgos para AAPL y NVDA.

## 🚀 Próximo Paso (Etapa 2)
Desarrollo de los **Servicios y Lógica de Negocio**, específicamente el `ValuationService` (Cálculo de Flujo de Caja Descontado / DCF basándose en el Excel de Valoración del usuario) y el `PortfolioService` (Cálculo real de Ganancias/Pérdidas).
