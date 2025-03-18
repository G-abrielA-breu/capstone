import numpy as np
import pandas as pd
from sklearn.datasets import make_blobs
from sklearn.cluster import KMeans
import plotly.express as px

# Generate synthetic data
n_samples = 300
n_features = 2
centers = 3
X, y = make_blobs(n_samples=n_samples, n_features=n_features, centers=centers, random_state=42)

# Convert to DataFrame for easier handling
df = pd.DataFrame(X, columns=['Feature 1', 'Feature 2'])

# Perform KMeans clustering
kmeans = KMeans(n_clusters=centers, random_state=42)
df['Cluster'] = kmeans.fit_predict(X)

# Create an interactive scatter plot
fig = px.scatter(df, x='Feature 1', y='Feature 2', color='Cluster', title='Interactive Cluster Diagram')
fig.show()