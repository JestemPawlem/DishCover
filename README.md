# DishCover - FullStack Recipe Recommender

A full stack web application for discovering, searching and receiving personalized culinary recommendations. Built with **FastAPI**, **React**, **PostgreSQL** and **PyTorch** Two-Tower recommendation pipeline trained on the [Food.com Recipes and Interactions](https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions) dataset from Kaggle.

## Key Features

 - **Popular Recipes**: Historical interactions from the dataset allow both guests and registered users to browse top-rated recipes.
 - **Personalized Recommendations**: Authenticated users can like recipes to shape their culinary profile and receive tailored suggestions.
 - **Item-to-Item Similarity**: Discover matching dishes with comparable ingredients and flavors while viewing any recipe.
 - **Fuzzy Full-Text Search**: Fast, typo-tolerant recipe search by title.
 - **Dual-Mode Containerization**: Docker Compose setup supporting a live-reloading Vite development environment and a production-ready **Nginx** static SPA deployment.

*(Note: The current MVP focuses strictly on discovery and recommendation workflows; user-submitted recipes and author profiles are outside the current scope).*

## System Architecture & Tech Stack

| Layer | Technology | Role |
| :--- | :--- | :--- |
| **Frontend** | React, TypeScript, Vite, Nginx | SPA UI; served via Vite in `dev` and Nginx in `prod`. |
| **Backend** | Python 3.12, FastAPI, Psycopg 3 | REST API, JWT authentication. |
| **Database** | PostgreSQL 16 (`pgvector`, `pg_trgm`) | Persistent storage, `vector` HNSW index, and `GIN` trigram index. |
| **ML Pipeline** | PyTorch, Pandas, Scikit-learn, SentenceTransformers, NLTK | Ingredient lemmatization & clustering, Two-Tower architecture, and batch embedding generation. |

## Machine Learning & Recommendation Design

The system decouples offline representation learning from online retrieval. PyTorch is used offline to learn ingredient-aware recipe embeddings from user interactions, while online serving bypasses neural network inference entirely in favor of centroid-based vector search in PostgreSQL.

### 1. Semantic Ingredient Normalization (NLP)

Raw ingredients in the dataset exhibit high variance and synonyms. The preprocessing pipeline standardizes the vocabulary before training:
 - **Text Cleaning & Lemmatization:** Strips numbers and punctuation, standardizing tokens using **NLTK WordNetLemmatizer**.
 - **Semantic Deduplication:** Encodes cleaned ingredient strings with **SentenceTransformers (`all-MiniLM-L6-v2`)** and groups synonyms via **Agglomerative Clustering** (cosine metric). Each cluster maps to a single canonical ingredient ID.

### 2. Recipe Representation Learning (PyTorch)

Rather than serving a live two-tower model for users lacking metadata, the neural network is trained to produce $N$-dimensional recipe representations:
 - **Feature Fusion:** Each recipe representation combines a learnable recipe ID embedding and `nn.EmbeddingBag` (mean-pooled embeddings of its canonical ingredients), projected through an MLP into an $L_2$-normalized latent space.
 - **Regularization via Dropout:** Recipe ID embeddings are masked during training. This forces the network to learn semantic relationships from ingredient compositions.
 - **Contrastive Optimization:** The model trains on interaction pairs using **InfoNCE loss** over in-batch negatives with temperature scaling and the **AdamW** optimizer.

### 3. Vector Serving & Online Retrieval
- **Precomputed Vector Index:** All recipe embeddings are precomputed offline and ingested into PostgreSQL, backed by an **HNSW index** with cosine distance (`vector_cosine_ops`).
- **Real-Time Taste Profiling:** An authenticated user's preference is represented by the centroid (mean vector) of all dishes they have liked.
- **Item-to-Item Discovery:** Individual recipe detail views execute an ANN search using the selected recipe's embedding, returning alternatives with overlapping flavor profiles.

## Retrospective & Known Limitations

- **Centroid Aggregation vs. Multi-Modal Tastes:** Representing a user as the arithmetic mean of their liked recipe embeddings is computationally lightweight and works well when a user has focused preferences. However, averaging can penalize diverse culinary tastes.
- **Model Precision & Noise:** The current Two-Tower model provides a solid baseline. It reliably captures distinct categories, though it occasionally surfaces noisy or unrelated dishes within the top-$k$.
- **Dataset Formatting Artifacts:** The raw Food.com dataset stores titles and descriptions entirely in lowercase and provides ingredient lists as raw tokens without exact culinary measurements.

## Getting Started

### 1. Environment Configuration

Clone the example environment.

### 2. First-Time Initialization (Data, ML Training & DB Seeding)
Before using the application for the first time, start the PostgreSQL database and run the batch ML pipeline to download the dataset, train the model, generate embeddings, and seed the database.

```bash
# 1. Start the PostgreSQL container
docker compose up -d postgres

# 2. Download the Kaggle dataset and preprocess recipes/interactions
docker compose run --rm ml-pipeline uv run python scripts/preprocess.py

# 3. Train the Two-Tower model and export recipe embeddings
docker compose run --rm ml-pipeline uv run python scripts/train.py

# 4. Bulk-seed PostgreSQL and build GIN / HNSW indexes
docker compose run --rm ml-pipeline uv run python scripts/seed_db.py
```

## Running the Application

The frontend uses a multi-stage `Dockerfile` to separate development and production workflows.

### Development Mode (Vite + Hot Module Replacement)
Runs the Vite development server with volume bind-mounts and file polling enabled for instant live reloading:

```bash
docker compose up -d --build frontend backend
```
- **Frontend (Vite Dev Server):** [http://localhost:5173](http://localhost:5173)
- **Backend API & Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **PostgreSQL (Host Port):** `localhost:5433`

### Production Mode (Nginx Static Build)
Compiles the TypeScript/React bundle into static assets and serves them via **Nginx** on port `80`, routing `/api/` requests internally to the FastAPI backend:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```
- **Application (Nginx):** [http://localhost](http://localhost) (Port 80)

### Stopping the Containers
```bash
docker compose down
```