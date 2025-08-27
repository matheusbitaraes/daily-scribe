## Section 1: Deconstructing Relevance in News Recommendation

### 1.1. Introduction: Beyond Simple Similarity

The task of creating a personalized news feed extends far beyond simple keyword matching or document similarity. A truly effective system must deliver content that is not only interesting but also timely, trustworthy, and novel. This represents a multi-objective optimization challenge where the system must balance several, often competing, definitions of "relevance" to build and maintain long-term user engagement and trust.1 A recommendation that is semantically perfect but a week old is useless in a breaking news context. A timely article from an untrustworthy source can erode user confidence. A stream of highly similar articles, while relevant, creates a monotonous "filter bubble" that limits discovery and leads to user fatigue.2

Therefore, a robust architecture for news curation must be built upon a multi-faceted understanding of relevance. This report deconstructs this complex concept into four foundational pillars, each of which will be translated into a quantifiable signal within the recommendation pipeline:

1. **Personalization (Semantic & Topical Match):** This pillar addresses the core question: "Is this article about subjects and concepts that are interesting *to this specific user*?" It requires a deep understanding of user preferences, captured through their interaction history.
2. **Timeliness (Temporal Relevance):** This pillar answers the question: "Is this article relevant *right now*?" The value of news decays over time, and this signal ensures that the recommendations are fresh and current.4
3. **Credibility (Source Authority):** This pillar tackles the critical issue of trust: "Is this article from a *trustworthy and authoritative source*?" In an era of widespread misinformation, prioritizing credible journalism is essential for platform integrity.5
4. **Novelty (Serendipity & Diversity):** This pillar addresses user experience and discovery: "Is this article *new and surprising*, or is it just another echo of what the user has already seen?" This involves actively working against redundancy to surface unexpected yet relevant content.2

By systematically engineering signals for each of these pillars and then intelligently fusing them, the daily-scribe project can evolve from a content aggregator into a sophisticated, personalized news curator.

### 1.2. The Daily-Scribe System Architecture: From Data to Decision

Building upon the existing capabilities for article storage, summarization, and embedding generation, the proposed relevance architecture can be conceptualized as a multi-stage pipeline. This pipeline is designed to efficiently process a large corpus of incoming news articles and deliver a small, highly curated list to each user.

The four primary stages of this pipeline are:

1. **Candidate Generation:** This initial stage is responsible for narrowing down the vast pool of all available news articles to a manageable subset of several hundred candidates for each user. This is a coarse filtering step that can be implemented using efficient methods. For example, it could involve a broad similarity search using the user's profile vector against all recent article embeddings or filtering based on high-level topic preferences. The goal is speed and recall—ensuring all potentially relevant articles make it to the next stage.
2. **Signal Generation & Scoring:** For each candidate article that passes the generation stage, the system will compute a set of scores corresponding to the four pillars of relevance. This is the heart of the feature engineering process. At this stage, the system calculates:
    - A **Semantic Similarity Score** based on the distance between the user's profile vector and the article's embedding.
    - A **Temporal Relevance Score** based on a time-decay function.
    - A **Source Authority Score** based on a heuristic model of credibility.
    - A **Topical Match Score** based on keyword or topic overlap.
3. **Ranking & Fusion:** This stage takes the multiple scores generated for each candidate article and combines them into a single, final relevance score. This can be achieved through two primary methods, which represent an evolution in system complexity:
    - **Weighted Linear Model:** A straightforward, interpretable approach where the final score is a weighted sum of the individual signal scores. This is an excellent starting point.
    - **Learning to Rank (LTR) Model:** A more advanced machine learning approach where a meta-model is trained on user interaction data to learn the optimal combination of signal scores, capturing complex, non-linear relationships between them.7
4. **Post-Processing & Re-ranking:** After the articles are sorted by their final relevance score, a final re-ranking step is applied to the top N results. This stage is designed to enhance the quality of the final list presented to the user. A key process here is the application of an algorithm like **Maximal Marginal Relevance (MMR)** to improve the diversity of the top-ranked articles, ensuring the user sees a variety of relevant content rather than several near-duplicates.9

This modular architecture provides a clear roadmap for development. The subsequent sections of this report will provide detailed technical proposals for implementing each component within this framework, starting with the most critical element: the user profile.

## Section 2: The User Profile Vector: The Cornerstone of Personalization

To deliver personalized content, the system must first understand the user. This understanding must be captured in a dynamic, machine-readable format that represents a user's evolving interests. The user profile is this representation, serving as the reference point against which all candidate articles are measured. A powerful profile is not a single entity but a hybrid construct, combining dense semantic representations with sparse, interpretable topic models.11

### 2.1. Foundational Approaches to User Profile Creation

Two complementary methods can be used to build a comprehensive user profile from their interaction history (e.g., articles they have read, saved, or explicitly "liked").

### 2.1.1. The Averaged Embedding Model: Capturing Semantic "Vibe"

The most direct way to create a user profile in the semantic space is to compute a central vector that represents their interests. This is achieved by averaging the document embeddings of articles the user has positively engaged with.14 This resulting "user profile vector" acts as a centroid of the user's interests in the high-dimensional vector space, capturing their overall semantic "vibe" or taste.11 If two texts have similar meanings, their embeddings will be close together in this space; consequently, a user's profile vector will be closer to articles that align with the general themes of their reading history.16

Implementation:

The process is computationally straightforward. Given a list of document embeddings for articles a user has liked, the average can be calculated using a library like NumPy.

*Pseudo-code for Averaged Embedding Profile:*

Python

# 

```
import numpy as np

def create_user_profile_vector(liked_article_embeddings: list) -> np.ndarray:
    """
    Creates a user profile vector by averaging the embeddings of liked articles.

    Args:
        liked_article_embeddings: A list of numpy arrays, where each array is an
                                  embedding of an article the user liked.

    Returns:
        A single numpy array representing the user's profile vector.
    """
    if not liked_article_embeddings:
        return None # Handle case for new users with no history

    # Stack embeddings into a single matrix
    embedding_matrix = np.vstack(liked_article_embeddings)

    # Calculate the mean across the rows (axis=0)
    user_profile_vector = np.mean(embedding_matrix, axis=0)

    return user_profile_vector

# Example Usage:
# Assume article_embeddings is a dictionary mapping article_id to its embedding vector
# and user_likes is a list of article_ids the user has liked.

liked_embeddings = [article_embeddings[article_id] for article_id in user_likes]
user_vector = create_user_profile_vector(liked_embeddings)

```

This method is simple to implement and surprisingly effective as a baseline for capturing broad user interests. However, its primary weakness lies in the nature of averaging. If a user has diverse interests—for example, reading deeply about both international politics and professional tennis—the resulting average vector may represent a nonsensical midpoint between these topics. Niche interests can be "averaged out," leading to a generic profile that recommends mainstream content at the expense of the specific topics that truly engage the user.

### 2.1.2. Topic-Based Profiling: Capturing Explicit Interests

To counteract the smoothing effect of averaging embeddings, a complementary, sparse profile should be created. This profile explicitly represents *what* topics a user is interested in, rather than just their general semantic location. This approach provides a more interpretable and precise representation of user interests.

Keyword Extraction with TF-IDF:

A foundational method for this is Term Frequency-Inverse Document Frequency (TF-IDF). TF-IDF is a statistical measure that evaluates how relevant a word is to a document within a collection of documents.18 It works by multiplying two metrics:

- **Term Frequency (TF):** How often a word appears in a specific document. A higher frequency suggests greater importance within that document.
- **Inverse Document Frequency (IDF):** A measure of how common or rare a word is across the entire corpus of documents. Common words like "the" or "is" appear in many documents and receive a low IDF score, while rare, specific terms receive a high score.18

By applying TF-IDF to the collection of articles a user has read, the system can extract a set of high-scoring keywords that characterize their interests. The user's profile then becomes a weighted list of these keywords, which can be directly compared against the keywords of new articles. It is crucial that the IDF component be calculated over a large, representative corpus of news articles, not just the user's reading history, to be meaningful.21

Advanced Topic Modeling with BERTopic:

While TF-IDF is effective, a more advanced and powerful approach is to use a modern topic modeling algorithm like BERTopic.23 Unlike traditional methods such as Latent Dirichlet Allocation (LDA), which rely on a "bag-of-words" model and require extensive text preprocessing, BERTopic leverages contextual embeddings from transformer models like BERT.24

This provides several key advantages in this context:

- **Semantic Coherence:** BERTopic creates topics by clustering document embeddings. This means that documents are grouped based on their semantic meaning, resulting in topics that are far more coherent and interpretable than those from LDA.24
- **Reduced Preprocessing:** Because it works with contextual embeddings, BERTopic does not require intensive preprocessing like stemming, lemmatization, or stop-word removal, simplifying the data pipeline.24
- **Automatic Topic Number Detection:** A significant challenge with LDA is pre-defining the number of topics. BERTopic can automatically determine the optimal number of topics from the data, making it more robust and adaptable.24

Using BERTopic, the system can model the entire news corpus to discover a set of underlying topics. Each user's profile can then be represented as a probability distribution across these topics, based on the articles they have read. This provides a rich, interpretable, and semantically-aware representation of their specific interests.

### 2.2. Dynamic Profile Updates for Evolving Interests

User interests are not static; they shift based on current events, new hobbies, or changing professional needs.12 A user who was interested in election coverage in November may be focused on holiday travel in December. Therefore, the user profile must be a living entity, dynamically updating to reflect these changes and prioritizing recent interactions over older ones.29

Implementation with Moving Averages:

To keep the user profile current, its calculation should incorporate a time-weighting mechanism.

- **Simple Moving Average (SMA):** The most basic approach is to define the user profile as the average of only the last 'N' articles the user has engaged with. For example, the profile is always the average of the 50 most recently read articles. This is simple to implement but can be overly sensitive to short-term reading binges and may abruptly "forget" long-term interests if the window size 'N' is too small.
- **Exponential Moving Average (EMA) / Exponential Decay:** A more sophisticated and stable method is the Exponential Moving Average. This approach updates the profile vector each time a user interacts with a new article, blending the new information with the existing profile. The update rule is as follows 30:
    
    Vnew_profile=α⋅Vnew_article+(1−α)⋅Vold_profile
    
    Here, V represents a vector, and α is a "smoothing factor" or learning rate between 0 and 1. A higher α gives more weight to the most recent article, causing the profile to adapt quickly, while a lower α results in a more stable profile that changes slowly. This method elegantly ensures that the influence of older articles decays exponentially over time without ever being completely discarded.
    

Online Learning and Incremental Updates:

For computational efficiency, a common practice in large-scale recommender systems is to perform online updates.31 In this paradigm, the embedding vectors for all articles (the "item vectors") are pre-computed and held static. When a user interacts with an article, only that specific user's profile vector needs to be updated. Since the update calculation for a single user is extremely fast (a simple vector addition and scalar multiplication), the system can reflect changes in user preference in near real-time without the need for costly daily retraining of the entire model ecosystem.31

The most effective user profile combines these different representations to create a more holistic view of the user. The dense vector from the averaged embedding model captures the user's broad, latent tastes—the *style* and *tone* of content they prefer. It excels at finding articles that "feel" right to the user, even if they are about a new topic. The sparse vector from the topic model, on the other hand, captures the user's specific, declared interests—the *subjects* they actively follow. It excels at identifying articles that are directly and explicitly relevant.

By maintaining these two profiles in parallel, the system can generate multiple, complementary relevance signals. When a new article is considered for recommendation, the system can calculate both its semantic similarity to the user's dense vector and its topical overlap with their sparse profile. These two distinct signals provide a much richer basis for the final ranking decision than either one could alone. This dual-profile approach not only improves recommendation accuracy but also lays the groundwork for more explainable AI, allowing the system to potentially surface justifications like, "Recommended because you are interested in 'Geopolitics' and articles with an analytical tone."

## Section 3: A Multi-Signal Approach to Article Scoring

Once a robust user profile is established, the next step is to score each candidate article against it. This scoring process should not rely on a single metric but should instead generate a suite of independent signals, each corresponding to one of the pillars of relevance. These signals are the raw, quantitative inputs for the final ranking model.

### 3.1. Signal 1: Semantic Similarity

This is the primary personalization signal, quantifying the conceptual alignment between a user's interests and an article's content. It is calculated by measuring the proximity between the user's dense profile vector and the candidate article's document embedding in the high-dimensional vector space.11 The core principle is that smaller distances (or higher similarity scores) imply a better match.17

Choosing the Right Similarity Metric:

The choice of metric to calculate this proximity is a critical implementation detail, as different metrics capture different properties of the vectors.34 The fundamental rule is to use the similarity metric that aligns with the objective function used to train the embedding model itself.34

- **Cosine Similarity:** This is the most common metric for NLP and text-based recommendation systems.36 It measures the cosine of the angle between two vectors, effectively ignoring their magnitudes and focusing solely on their orientation or direction in the vector space. This is ideal for text, where vector direction captures the topic or semantic meaning, and magnitude (which can be influenced by document length) is often less important. The score ranges from -1 (opposite) to 1 (identical), with 0 indicating orthogonality (no relation).33 The formula is:
    
    sim(A,B)=∥A∥∥B∥A⋅B=∑i=1nAi2∑i=1nBi2∑i=1nAiBi
    
- **Euclidean Distance (L2 Distance):** This metric calculates the straight-line or "as-the-crow-flies" distance between the terminal points of two vectors in the n-dimensional space.33 It is sensitive to both magnitude and direction. A smaller distance implies greater similarity. While common in other domains like image recognition, it is less frequently used for modern text embeddings unless the vector magnitudes have a specific, intended meaning.34 The formula is:
    
    d(A,B)=∑i=1n(Ai−Bi)2
    
- **Dot Product (Inner Product):** This metric is the un-normalized version of cosine similarity. It is calculated as the sum of the products of the corresponding vector components and is influenced by both the angle between the vectors and their magnitudes.33 It is computationally the fastest of the three. For vectors that have been normalized to unit length (a common practice), the dot product is mathematically equivalent to cosine similarity. Many modern embedding models are trained to optimize for dot product similarity, making it the correct choice in those cases.34 The formula is:
    
    A⋅B=∑i=1nAiBi
    

The following table provides a clear comparison to guide the selection process.

| Metric | Measures | Typical Use Case | Computational Cost | Key Consideration |
| --- | --- | --- | --- | --- |
| **Cosine Similarity** | Direction only | NLP, Semantic Search, Text Recommendation | Moderate | Best when vector orientation (topic) is more important than magnitude (e.g., document length). |
| **Euclidean Distance** | Magnitude and Direction | Image Similarity, Signal Processing | High (due to square root) | Use when absolute difference in vector values is meaningful. Less common for modern text embeddings. |
| **Dot Product** | Magnitude and Direction | General Purpose, LLM Embeddings | Low (Fastest) | Often the default choice for normalized vectors or when the embedding model was trained to optimize it. |

### 3.2. Signal 2: Temporal Relevance (Time-Decay)

News is one of the most time-sensitive content domains. An article's relevance is highest at the moment of publication and decays rapidly thereafter.4 A news recommendation system that fails to account for this temporal decay will quickly feel stale and irrelevant. This signal must be a core component of the ranking function.

Implementing Time-Decay Functions:

The concept is to apply a mathematical function that reduces an article's score as it ages.40 While linear decay is possible, an exponential decay function more accurately models the rapid initial drop-off in relevance followed by a longer tail of diminishing value. A particularly effective and widely used formula, borrowed from marketing attribution models which face a similar problem of time-sensitive influence, is based on a configurable half-life.43

The proposed formula for the time-decay score (normalized between 0 and 1) is:

TimeScore=2−half_life_daysage_in_days

- **age_in_days:** The number of days that have passed since the article was published.
- **half_life_days:** A configurable parameter representing the time it takes for an article's temporal relevance to decay to 50% of its initial value.

Tuning the Half-Life:

The half_life parameter is a powerful tuning lever. A single, global half-life is a blunt instrument. A more sophisticated system should make this parameter dynamic, personalizing the decay rate based on the content's nature and potentially the user's preferences.

For instance, different news categories have different decay rates:

- **Breaking News:** A story about a market crash or a political event might have a `half_life` of just 1 or 2 days.
- **Investigative Journalism:** A long-form investigative piece might remain highly relevant for weeks or months, justifying a `half_life` of 30 or 60 days.
- **Evergreen Analysis:** An opinion piece or historical analysis might have an even longer `half_life`.

The system can implement this by maintaining a simple lookup table that maps article categories (or topics) to `half_life` values. This ensures that a timely but ephemeral story is prioritized appropriately, while an important but less time-sensitive analysis is not prematurely down-ranked. This creates a far more nuanced and effective timeliness signal than a one-size-fits-all approach.

### 3.3. Signal 3: Source Authority and Credibility

In the current information ecosystem, recommending content from credible, authoritative sources is not just a feature but a responsibility. To build user trust and deliver genuine value, the daily-scribe system must be able to distinguish between high-quality journalism and low-quality or misleading content. This requires operationalizing the abstract concept of "authority" into a quantifiable score.6

While services like Ad Fontes Media 44 and NewsGuard 45 employ teams of journalists for manual rating, a similar outcome can be approximated by engineering a proxy score from programmatically accessible signals. This score can be constructed as a weighted combination of the following features:

1. **Original Reporting Signal:** Google's topic authority system identifies original reporting by tracking how a story is cited by other publishers.5 A similar heuristic can be implemented by analyzing inbound links. For a given article, the system can count the number of hyperlinks pointing to it from other known news domains within a short time window (e.g., 72 hours) of its publication. A high count of such links is a strong indicator that the article broke a story or provided unique, valuable reporting that others are referencing.
2. **Source Reputation Signal:** A tiered system can be created to score the general reputation of the news source itself. This involves manually curating a list of sources and assigning them to tiers:
    - **Tier 1 (Highest Score):** Globally recognized wire services and publications with a long history of high-quality, original reporting (e.g., Associated Press, Reuters, BBC, The New York Times). These sources often have rigorous editorial standards.46
    - **Tier 2 (Medium Score):** Reputable national and regional news organizations.
    - Tier 3 (Base Score): All other news sources.
        
        This tier can be augmented by programmatic signals like the presence of journalistic awards or recommendations from professional societies mentioned on the source's website.5
        
3. **Domain Authority (SEO Proxy):** While not a direct measure of journalistic integrity, metrics from the world of Search Engine Optimization (SEO) can serve as a useful proxy for a source's established influence and general trustworthiness. Third-party tools like Semrush provide an "Authority Score" based on backlink quality and quantity, organic traffic, and other signals.48 A higher score generally indicates a more established and influential web presence. This metric can be integrated via API to provide a continuous measure of a source's online footprint.
4. **Transparency Signals:** Professional rating criteria heavily weigh transparency.45 The system can perform simple checks on each source's website to award points for the presence of:
    - An easily accessible "About Us" or "Mission Statement" page.
    - A clear and public corrections policy.
    - Identifiable author bylines on articles, preferably linked to author biographies.
        
        The presence of these elements signals adherence to basic journalistic practices and contributes to a higher authority score.
        

By combining these four signals, the system can generate a robust, heuristic-based **Source Authority Score** for each article, providing a vital layer of quality control in the recommendation process.

## Section 4: Fusing Signals into a Unified Ranking Score

With a set of independent scores for semantic similarity, temporal relevance, source authority, and topical match for each candidate article, the final task is to fuse them into a single, sortable score. This unified score will determine the final ranking of articles presented to the user. Two primary strategies exist for this fusion, representing a progression from a simple, interpretable baseline to a more powerful, data-driven machine learning approach.

### 4.1. Proposal A: The Weighted Linear Model

This approach is the most direct, transparent, and easiest to implement, making it an ideal starting point. The final relevance score is calculated as a simple weighted sum of the individual, normalized signal scores.51

The governing formula would be:

FinalScore=(wsim⋅SimScore)+(wtime⋅TimeScore)+(wauth⋅AuthScore)+(wtopic⋅TopicMatchScore)

Where `w` represents the weight assigned to each signal, controlling its influence on the final score.

**Implementation Steps:**

1. **Normalization:** Before they can be combined, each raw signal score must be normalized to a common scale, typically 0 to 1. For instance, the semantic similarity score (e.g., cosine similarity) is already in a suitable range, but the source authority score might be on a 1-100 scale and would need to be divided by 100. This ensures that no single signal dominates the final score simply due to its scale.
2. **Weight Setting:** The weights (`w_sim`, `w_time`, etc.) are the hyperparameters that tune the behavior of the recommender. A good starting point is the "equal contribution" baseline strategy.51 This does not mean setting all weights to 1.0. Instead, it involves adjusting the weights so that, on average, each component contributes a similar amount to the final score. For example, if the average normalized
    
    `SimScore` is 0.7 and the average `TimeScore` is 0.2, their initial weights might be set to 1.0 and 3.5 respectively, to balance their typical impact.
    
3. **Manual Tuning:** These weights should be exposed as configurable parameters. The initial balance can be tuned through qualitative evaluation ("Does this ranking *feel* right?") and later refined based on implicit user feedback (e.g., if users are consistently ignoring older articles, the `w_time` might need to be increased). The primary advantage of this model is its interpretability; if the recommendations are poor, it is straightforward to diagnose which signal might be over- or under-weighted.

### 4.2. Proposal B: Transitioning to Learning to Rank (LTR)

While the weighted model is an excellent baseline, its performance is limited by the manual tuning of weights. It cannot capture complex, non-linear interactions between signals (e.g., perhaps source authority is much more important for political news than for sports news). A Learning to Rank (LTR) model overcomes this by using machine learning to learn the optimal ranking function directly from user interaction data.7

In the LTR paradigm, the signals engineered in the previous section (SimScore, TimeScore, AuthScore, etc.) are no longer combined with a simple formula. Instead, they become a *feature vector* that describes each user-article pair. A machine learning model is then trained on historical data (e.g., logs of which articles users clicked on) to predict the best ordering of articles based on these features.57

There are three main families of LTR algorithms, which differ in how they approach the loss function during training.

- **Pointwise Approach:** This is the simplest LTR method. It treats ranking as a regression or classification problem on individual documents. The model takes the feature vector for a single user-article pair and predicts an absolute relevance score (e.g., "7.5 out of 10") or a class (e.g., "will click" vs. "won't click").59 The final list is then sorted by these predicted scores. Its main drawback is that it completely ignores the relative ordering of other documents in the list; the score for one document is calculated in isolation from all others, which is not how users perceive a ranked list.61
- **Pairwise Approach:** This approach more closely models the nature of ranking. Instead of predicting an absolute score, the model takes a *pair* of documents for a given user and learns to predict which of the two is more relevant.60 The training data consists of pairs of documents
    
    `(DocA, DocB)`, where the label indicates whether the user preferred A over B. The model's objective is to minimize the number of incorrectly ordered pairs in the final ranking. This approach is more powerful than pointwise because it directly optimizes for relative order. Prominent algorithms like RankNet, LambdaRank, and LambdaMART use this approach and represent a practical sweet spot between performance and complexity.60
    
- **Listwise Approach:** This is the most theoretically sound but also the most complex approach. The model considers the entire list of candidate documents at once and attempts to directly optimize a list-based ranking metric, such as Normalized Discounted Cumulative Gain (NDCG).60 It learns to predict the optimal permutation of the entire list. While this can lead to the best performance, the complexity of the loss functions and the computational cost of training can be significantly higher.57

The following table summarizes the trade-offs between these LTR strategies.

| Approach | Core Idea | Loss Function Example | Pros | Cons |
| --- | --- | --- | --- | --- |
| **Pointwise** | Predict absolute relevance for single documents (Regression/Classification) | Mean Squared Error (MSE) | Simple to implement; leverages standard ML algorithms. | Ignores the relative context of other documents; doesn't directly optimize ranking metrics. |
| **Pairwise** | Predict the relative order of document pairs (Binary Classification) | Binary Cross-Entropy (RankNet) | Better performance than pointwise; directly models relative preference; computationally efficient. | Doesn't optimize the global list structure; can lead to minor inconsistencies in the full ranking. |
| **Listwise** | Optimize the entire ranked list of documents directly | ListNet Loss (Cross-Entropy over permutations) | Theoretically optimal; directly optimizes ranking metrics like NDCG. | High computational complexity; more difficult to implement and train. |

For the daily-scribe project, a strategic evolution is recommended. Begin with the simple Weighted Linear Model (Proposal A). In parallel, begin logging the necessary user interaction data (impressions, clicks, dwell time) along with the feature vectors for each article. Once sufficient data is collected, transition to a Pairwise LTR model like LambdaMART (Proposal B). This provides a significant performance improvement by moving from a heuristic to a data-driven ranking function, without incurring the full complexity of a listwise implementation.

## Section 5: Post-Processing and Refining the Final Recommendation List

Generating a list of articles sorted by a relevance score is the penultimate step. A final post-processing stage is crucial to transform this ranked list into a high-quality user experience. This involves addressing issues of content diversity and ensuring the underlying technical architecture is robust and scalable.

### 5.1. Ensuring Diversity with Maximal Marginal Relevance (MMR)

A common failure mode of relevance-based ranking is redundancy. If a user is interested in "advances in artificial intelligence," a purely relevance-focused model might return five articles that are all slight variations of the same press release about a new model.10 This creates a poor user experience and traps the user in a "filter bubble," limiting their discovery of new information.2

Maximal Marginal Relevance (MMR) is a re-ranking algorithm designed specifically to combat this problem by promoting diversity in the top results.9 MMR works by iteratively building the final recommendation list. In each step, it selects the next item not based on its raw relevance score alone, but on a combination of its relevance to the user's profile and its

*dissimilarity* to the items already selected for the list.10

The MMR Formula:

The selection criterion for the next document to add to the list is governed by the following formula 64:

$MMR = \underset{D_i \in R \setminus S}{\operatorname{argmax}} \left$

Let's break down the components:

- Di: A candidate document from the original ranked list (R) that has not yet been selected for the final list (S).
- Sim(Di,Q): The original relevance score of the candidate document Di with respect to the user query/profile Q. This is the "relevance" term.
- Dj∈Smax(Sim(Di,Dj)): The maximum similarity between the candidate document Di and any document Dj *already in the selected list S*. This is the "redundancy" or "similarity" term.
- λ (lambda): A tuning parameter between 0 and 1 that controls the trade-off between relevance and diversity.
    - If λ=1, the second term is ignored, and the algorithm simply performs a standard relevance ranking.
    - If λ=0, the first term is ignored, and the algorithm selects for maximum diversity without regard for relevance.
    - A value such as λ=0.7 provides a balance, prioritizing relevance but penalizing candidates that are too similar to already selected results.10

Implementation:

MMR should be applied as a final re-ranking step, not as a replacement for the primary ranking model. The most efficient implementation is to first generate a list of the top K candidate articles (e.g., K=50) using the fused relevance score from the LTR or weighted model. Then, apply the iterative MMR algorithm to this smaller set of 50 candidates to select the final top N (e.g., N=10) to display to the user. This approach provides the benefits of diversity with a minimal computational overhead, as the expensive pairwise similarity calculations are only performed on a small subset of documents.65

### 5.2. System Architecture and Tooling

The performance and scalability of the entire relevance system depend heavily on the choice of underlying infrastructure, particularly for handling vector embeddings.

Vector Databases:

Storing and searching through millions of high-dimensional document embeddings requires a specialized database designed for this task.37 A standard relational database is not equipped for efficient nearest-neighbor search. The system should leverage a dedicated vector database.

Key options include:

- **Managed Services (e.g., Pinecone, Qdrant Cloud, Milvus Cloud):** These offer a fully managed infrastructure, abstracting away the complexities of scaling and maintenance. They are excellent for rapid development and production deployment.71 Qdrant, for example, is noted for its high performance due to its Rust-based architecture and offers a flexible API that is well-suited for recommendation tasks.33
- **Open-Source Self-Hosted (e.g., Qdrant, Milvus):** These provide maximum flexibility and control but require more operational overhead for deployment, scaling, and maintenance.
- **Standalone Libraries (e.g., FAISS):** FAISS (Facebook AI Similarity Search) is a highly efficient library for similarity search and indexing but is not a full-fledged database.16 It lacks features like CRUD operations, metadata filtering, and fault tolerance that are critical for a production application.72

When selecting a vector database, the following features are critical:

- **Approximate Nearest Neighbor (ANN) Indexing:** For large datasets, searching for the exact nearest neighbors for a query vector is too slow. ANN algorithms like HNSW (Hierarchical Navigable Small World) provide a trade-off between speed and accuracy, enabling fast retrieval with near-perfect results.70
- **Metadata Filtering:** The ability to store and filter on metadata alongside the vectors is crucial. This allows the system to perform hybrid searches, for example, finding articles that are semantically similar *and* were published in the last 24 hours *and* are from a Tier 1 source.
- **Scalability and Cost-Efficiency:** The database must be able to scale horizontally as the number of articles grows. Features like quantization and on-disk storage can dramatically reduce memory usage and operational costs.71

Embedding Models:

The quality of the document embeddings is foundational to the entire personalization system. The choice of which model to use involves trade-offs between performance, cost, and speed.

- **Proprietary Models (e.g., OpenAI, Cohere):** Services like OpenAI's `text-embedding-3` series offer state-of-the-art performance and are easy to use via an API call.73 They are an excellent choice for getting started quickly with high-quality embeddings.
- **Open-Source Models (e.g., from Hugging Face):** A vast number of pre-trained sentence-transformer models are available on platforms like Hugging Face. These offer more control and can be run on local infrastructure, eliminating API costs and latency. However, they require more effort to host and manage.

When choosing a model, consider the following trade-offs 74:

- **Performance vs. Size:** Larger models generally provide better retrieval quality (higher accuracy) but have higher latency and require more computational resources.
- **Embedding Dimensionality:** Higher-dimensional vectors can capture more nuance but require more storage and can be slower to search. Many modern models offer variable dimensions.
- **Cost:** API-based models have a per-use cost, while self-hosting has an upfront and ongoing infrastructure cost.

A practical approach is to begin with a high-performing, cost-effective proprietary model (like OpenAI's `text-embedding-3-small`) and establish a pipeline that allows for swapping in different models as needs evolve or as better open-source alternatives become available.

## Section 6: Strategic Recommendations and Implementation Roadmap

This section synthesizes the preceding analysis into a concrete, phased implementation plan. This roadmap is designed to deliver value incrementally, allowing the daily-scribe project to launch a functional relevance engine quickly and then progressively enhance its sophistication over time.

### 6.1. Phased Implementation Plan

The development of the relevance engine can be broken down into three distinct phases, each building upon the last.

Phase 1: Minimum Viable Relevance (Weeks 1-4)

The goal of this phase is to rapidly deploy a functional, personalized recommendation system. The focus is on simplicity, interpretability, and speed of implementation.

- **User Profile:** Implement the **Averaged Embedding** user profile. Use an **Exponential Moving Average (EMA)** for dynamic updates to ensure the profile adapts to recent user activity.
- **Signals:** Implement the two most critical signals:
    1. **Semantic Similarity:** Use Cosine Similarity to measure the distance between the user's profile vector and candidate article embeddings.
    2. **Temporal Relevance:** Implement the exponential **Time-Decay** function with a fixed, global `half_life` (e.g., 7 days) as a starting point.
- **Fusion:** Use the **Weighted Linear Model** to combine the two signals. The weights will be tuned manually based on qualitative evaluation of the output.
- **Tech Stack:**
    - Select and integrate an embedding model (e.g., OpenAI's `text-embedding-3-small` for a balance of performance and cost).
    - Set up a managed vector database (e.g., Qdrant Cloud) to store and query article embeddings.

Phase 2: Enhancing Signal Quality & User Experience (Weeks 5-10)

With the core system in place, this phase focuses on improving the quality and diversity of the recommendations by incorporating more nuanced signals.

- **Signals:**
    1. Develop and integrate the proxy **Source Authority Score** as a third signal into the weighted model. This will immediately improve the credibility of recommended content.
    2. Implement a **Personalized Time-Decay** function where the `half_life` varies based on the article's category (e.g., "Breaking News" vs. "Opinion").
- **Refinement:** Implement **Maximal Marginal Relevance (MMR)** as a post-ranking step on the top 50 results to improve list diversity and reduce redundancy.
- **User Profile:**
    1. Implement a parallel **BERTopic-based** topic model on the article corpus.
    2. Create a sparse topic-based user profile.
    3. Add a **Topical Match Score** as a fourth signal to the weighted model, further improving personalization.

Phase 3: Transition to Machine-Learned Ranking (Weeks 11+)

This phase represents the maturation of the system, moving from a heuristic-based model to a fully data-driven, self-optimizing ranking engine.

- **Data Collection:** Begin logging the necessary training data. For every article impression, log the user ID, the article ID, the explicit outcome (click/no-click, save, etc.), and the full feature vector (the four signal scores from Phases 1 & 2).
- **Model Training:** Once a sufficient volume of interaction data is collected, train an initial **Pairwise Learning to Rank (LTR)** model (e.g., using a library that implements LambdaMART). This model will learn the optimal weights and interactions between the features.
- **Deployment & Iteration:** Replace the manual Weighted Linear Model with the trained LTR model for scoring. Establish a continuous improvement loop where the LTR model is periodically retrained on fresh data, and new features (signals) can be engineered and incorporated over time.

This phased approach provides a structured path from a simple but effective system to a state-of-the-art, machine-learned relevance engine, ensuring that the daily-scribe project can deliver increasing value to its users at each stage of its development.

The following table provides a high-level overview of this implementation roadmap.

| Phase | Key Objectives | Estimated Timeline |
| --- | --- | --- |
| **Phase 1: Minimum Viable Relevance** | - Implement Averaged Embedding user profile with EMA updates. 
 - Deploy Semantic Similarity and basic Time-Decay signals. 
 - Use a manually tuned Weighted Linear Model for ranking. 
 - Integrate vector DB and embedding model. | Weeks 1-4 |
| **Phase 2: Enhancing Signal Quality & UX** | - Develop and integrate the proxy Source Authority score. 
 - Implement MMR re-ranking for list diversity. 
 - Add a parallel BERTopic-based user profile and Topical Match signal. 
 - Refine Time-Decay with category-specific half-lives. | Weeks 5-10 |
| **Phase 3: Transition to ML Ranking** | - Establish a pipeline for logging user interactions as LTR training data. 
 - Train an initial Pairwise LTR model (e.g., LambdaMART). 
 - Replace the weighted model with the LTR model in production. 
 - Set up a recurring model retraining and evaluation process. | Weeks 11+ |