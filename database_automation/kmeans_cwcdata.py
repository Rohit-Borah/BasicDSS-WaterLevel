# import pandas as pd
# import matplotlib.pyplot as plt
# from sklearn.preprocessing import StandardScaler
# from sklearn.impute import SimpleImputer
# from sklearn.cluster import KMeans
# from sklearn.decomposition import PCA
# import numpy as np

# # === Load your CSV ===
# file_path = r"D:\MyWorkspace\Data Sets\test_csv_project3\water_level_bulletin.csv"  # Change to your actual path
# df = pd.read_csv(file_path)

# # === Select features for clustering ===
# features = [
#     "warning_level_m",
#     "danger_level_m",
#     "hfl_m",
#     "water_level_0800hrs_m",
#     "water_level_1800hrs_m",
#     "rainfall_mm",
# ]

# X = df[features]

# # === Handle missing values (mean imputation) ===
# imputer = SimpleImputer(strategy="mean")
# X_imputed = imputer.fit_transform(X)

# # === Standardize the data ===
# scaler = StandardScaler()
# X_scaled = scaler.fit_transform(X_imputed)

# # === Elbow Method (on sample for speed) ===
# sampled = pd.DataFrame(X_scaled).sample(n=1000, random_state=42).values
# inertia = []
# K_range = range(2, 11)

# for k in K_range:
#     kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
#     kmeans.fit(sampled)
#     inertia.append(kmeans.inertia_)

# plt.figure(figsize=(7,5))
# plt.plot(K_range, inertia, marker='o')
# plt.xlabel("Number of clusters (k)")
# plt.ylabel("Inertia")
# plt.title("Elbow Method for Optimal k")
# plt.grid(True)
# plt.show()

# # === Choose k manually (after inspecting elbow plot) ===
# optimal_k = 5  # <- change after checking elbow graph

# kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
# df["cluster"] = kmeans.fit_predict(X_scaled)

# # === Dimensionality reduction (PCA for visualization) ===
# pca = PCA(n_components=2)
# X_pca = pca.fit_transform(X_scaled)

# plt.figure(figsize=(8,6))
# plt.scatter(X_pca[:,0], X_pca[:,1], c=df["cluster"], cmap="tab10", alpha=0.7)
# plt.xlabel("PCA Component 1")
# plt.ylabel("PCA Component 2")
# plt.title(f"K-Means Clustering (k={optimal_k}) on Water Levels")
# plt.colorbar(label="Cluster")
# plt.show()

# # === Optional: Check cluster distribution ===
# print(df.groupby("cluster")[features].mean())

# # === Cluster feature means (already in script) ===
# cluster_means = df.groupby("cluster")[features].mean()
# print("\n=== Cluster Feature Means ===")
# print(cluster_means)

# # === Feature importance estimation (variance across clusters) ===
# feature_importance = cluster_means.var().sort_values(ascending=False)
# print("\n=== Feature Importance (based on variance across clusters) ===")
# print(feature_importance)

# # === Plot feature importance ===
# plt.figure(figsize=(8,5))
# feature_importance.plot(kind='bar')
# plt.ylabel("Variance across clusters")
# plt.title("Feature Importance for Cluster Separation")
# plt.xticks(rotation=45)
# plt.grid(True, axis='y')
# plt.show()



import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import numpy as np

# === Load your CSV ===
#file_path = r"D:\MyWorkspace\Data Sets\test_csv_project3\water_level_bulletin.csv"  # Change to your actual path
file_path = r"D:\MyWorkspace\Data Sets\test_csv_project3\bulletindata_25to8.csv"  # Change to your actual path
df = pd.read_csv(file_path)

# === Select features for clustering ===
features = [
    "warning_level_m",
    "danger_level_m",
    "hfl_m",
    "water_level_0800hrs_m",
    "water_level_1800hrs_m",
    "rainfall_mm",
]

X = df[features]

# === Handle missing values (mean imputation) ===
imputer = SimpleImputer(strategy="mean")
X_imputed = imputer.fit_transform(X)

# === Standardize the data ===
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_imputed)

# === Elbow Method (on sample for speed) ===
#sampled = pd.DataFrame(X_scaled).sample(n=1000, random_state=42).values
sampled = pd.DataFrame(X_scaled).sample(n=500, random_state=42).values
inertia = []
K_range = range(2, 11)

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(sampled)
    inertia.append(kmeans.inertia_)

plt.figure(figsize=(7,5))
plt.plot(K_range, inertia, marker='o')
plt.xlabel("Number of clusters (k)")
plt.ylabel("Inertia")
plt.title("Elbow Method for Optimal k")
plt.grid(True)
plt.show()

# === Choose k manually (after inspecting elbow plot) ===
optimal_k = 5 #3 #5  # <- change after checking elbow graph
print("\n=== Optimal K chosen ===")
print(optimal_k)

kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
df["cluster"] = kmeans.fit_predict(X_scaled)

# === Dimensionality reduction (PCA for visualization) ===
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

plt.figure(figsize=(25,22))
scatter = plt.scatter(X_pca[:,0], X_pca[:,1], c=df["cluster"], cmap="tab10", alpha=0.7)
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.title(f"K-Means Clustering (k={optimal_k}) on Water Levels")
plt.colorbar(scatter, label="Cluster")

# # Annotate a few stations for context (to avoid overcrowding, show 1 in 30)
# for i in range(0, len(df), 50):
#     plt.text(X_pca[i,0], X_pca[i,1], df["station"].iloc[i], fontsize=8, alpha=0.7)

plt.show()

# === Optional: Check cluster distribution by river/station ===
cluster_summary = df.groupby("cluster")[["river", "station"]].agg(list)
print("\n=== Stations grouped by cluster ===")
print(cluster_summary)
#cluster_summary.to_csv('Station_by_cluster.csv', index=True)
#cluster_summary.to_csv('Station_by_cluster_25to8.csv', index=True)

# === Mean values of features per cluster ===
cluster_means = df.groupby("cluster")[features].mean()
print("\n=== Cluster Feature Means ===")
print(cluster_means)
#cluster_means.to_csv('Cluster_feature_means.csv', index=True)
#cluster_means.to_csv('Cluster_feature_means_25to8.csv', index=True)

# === Feature importance estimation (variance across clusters) ===
feature_importance = cluster_means.var().sort_values(ascending=False)
print("\n=== Feature Importance (based on variance across clusters) ===")
print(feature_importance)
#feature_importance.to_csv('Feature_Importance.csv', index=True)
#feature_importance.to_csv('Feature_Importance_25to8.csv', index=True)

# === Plot feature importance ===
plt.figure(figsize=(8,5))
feature_importance.plot(kind='bar')
plt.ylabel("Variance across clusters")
plt.title("Feature Importance for Cluster Separation")
plt.xticks(rotation=45)
plt.grid(True, axis='y')
plt.show()
