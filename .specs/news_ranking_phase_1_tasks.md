# Phase 1: Minimum Viable Relevance — Task Breakdown

## 1. User Profile: Averaged Embedding with EMA Updates
- Implement a function to compute a user's profile vector as the (exponential) moving average of embeddings for articles they've interacted with.
- Store and update user profile vectors in a new table
- update logic in the user interaction pipeline to update the profile vector on each new interaction. Do it when generating the diggest

## 2. Semantic Similarity Signal
- Integrate or select an embedding model from openAI for generating article and user embeddings.
- Store article embeddings in a vector database (e.g., Qdrant Cloud) or a local vector store.
- Implement a function to compute cosine similarity between user profile vectors and article embeddings.

## 3. Temporal Relevance Signal (Time-Decay)
- Implement the exponential time-decay function for articles, using a fixed global half-life (e.g., 7 days).
- Add logic to compute the age of each article and apply the decay function to generate a time relevance score.

## 4. Weighted Linear Model for Fusion
- Implement a function to combine the semantic similarity and time-decay scores using a weighted sum.
- Make the weights configurable (e.g., via config file or environment variable).

## 5. Integration and Ranking
- Implement a candidate generation step: retrieve a set of recent articles for each user.
- For each candidate, compute the semantic similarity and time-decay scores, then combine them using the weighted model.
- Sort and return the top-N articles for the user.

## 6. Tech Stack Setup
- Integrate the chosen embedding model into the article ingestion pipeline.
- Set up and connect to the vector database for storing and querying embeddings.

## 7. Testing and Evaluation
- Write unit tests for each scoring function (profile update, similarity, time-decay, fusion).
- Add integration tests for the end-to-end ranking pipeline.
