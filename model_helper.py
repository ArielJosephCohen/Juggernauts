from cohen_code.import_modules import *


# classification
logreg = LogisticRegression()
xgbc = XGBClassifier()
rfc = RandomForestClassifier()
knnc = KNeighborsClassifier()
dtc = DecisionTreeClassifier()
svm = SVC()

# regression
linreg = LinearRegression()
xgbr = XGBRegressor()
rfr = RandomForestRegressor()
knnr = KNeighborsRegressor()
dtr = DecisionTreeRegressor()

# clustering
kmeans = KMeans()
msc = MeanShift()
scan = DBSCAN()

# neural network
keras_seq = Sequential()



def model_clean_pipeline(df):

    target2 = 'xG_a'
    target1 = 'xG_h'
    target3='outcome'

    df.drop([target1,target3],axis=1).select_dtypes(include=[float,int])
    #y1=df[target1]
    #y2=df[target2]
    y=df[target3]

    df.fillna(0,inplace=True)  


    for col in ['Unnamed: 0','h_h','a_a','a_h','h_a','home_team','goals_h','goals_a','forward_passes_attempted_a','c_h','l_H']:
        df.drop(col,axis=1,inplace=True,errors='ignore')

    df.reset_index(inplace=True,drop=True)  

    df=df.select_dtypes(include=[float,int])

    return df


def cluster_model(X, method='kmeans', n_clusters=3):

    # Initialize the clustering model based on the chosen method
    if method == 'kmeans':
        model = KMeans(n_clusters=n_clusters, random_state=42)
    elif method == 'meanshift':
        model = MeanShift()
    elif method == 'dbscan':
        model = DBSCAN()
    else:
        raise ValueError("Invalid method. Choose from 'kmeans', 'meanshift', or 'dbscan'.")

    # Fit the model and predict cluster labels
    labels = model.fit_predict(X)

    # Evaluation Metrics
    if len(set(labels)) > 1:  # Avoid metrics if only one cluster is found
        silhouette = silhouette_score(X, labels)
        calinski = calinski_harabasz_score(X, labels)
        print(f'Silhouette Score: {silhouette:.4f}')
        print(f'Calinski-Harabasz Index: {calinski:.4f}')
    else:
        print('Only one cluster found; silhouette score and calinski-harabasz index are not meaningful.')

    # Feature Importance
    if method in ['kmeans', 'meanshift']:
        if hasattr(model, 'cluster_centers_'):  # For KMeans and Mean Shift
            feature_importance = np.std(model.cluster_centers_, axis=0)
            feature_names = X.columns if isinstance(X, pd.DataFrame) else [f'Feature {i+1}' for i in range(X.shape[1])]

            importance_df = pd.DataFrame({
                'Feature': feature_names,
                'Importance': feature_importance
            }).sort_values(by='Importance', ascending=False)

            print("\nFeature Importance (based on cluster center variability):")
            print(importance_df)
            
            # Bar Plot of Feature Importance
            plt.figure(figsize=(10, 6))
            sns.barplot(data=importance_df, x='Importance', y='Feature', palette='viridis')
            plt.title(f'Feature Importance ({method.upper()})')
            plt.tight_layout()
            plt.show()

    # Visualizations
    # Scatter plot of clusters for the first two features
    plt.figure(figsize=(15, 8))
    unique_labels = set(labels)
    colors = sns.color_palette('hsv', len(unique_labels))

    for label, color in zip(unique_labels, colors):
        mask = labels == label
        plt.scatter(X[mask, 0], X[mask, 1], 
                    label=f'Cluster {label}', alpha=0.6, s=50, color=color)

    plt.title(f'Clusters Visualization ({method.upper()}) (First Two Features)')
    plt.xlabel('Feature 1')
    plt.ylabel('Feature 2')
    plt.legend(loc='best', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.show()

    # Cluster centers for KMeans and MeanShift
    if method in ['kmeans', 'meanshift'] and hasattr(model, 'cluster_centers_'):
        centers = model.cluster_centers_
        plt.scatter(centers[:, 0], centers[:, 1], 
                    c='black', s=200, alpha=0.7, marker='X', label='Centroids')
        plt.title('Cluster Centroids (First Two Features)')
        plt.legend(loc='best')
        plt.tight_layout()
        plt.show()


def classi_model(X, Y, choice='best', feature_selection='none', rocc=False, coef=False, feature_importance=False):
    # Ensure Y is binary by mapping 1 and 2 to 0 and 1
    if len(Y.unique()) > 2:
        print("Target variable should have only two unique classes. Mapping values to [0, 1]...")
        Y = Y.map({1: 0, 2: 1})  # Convert 1 -> 0, 2 -> 1

    # Check again if Y is binary
    if len(Y.unique()) != 2:
        print("Target variable is still not binary!")
        return

    # Standardize features if needed (using the custom pipeline for preprocessing)
    X = model_clean_pipeline(X)
    X_scaled = X  # Assuming X is already scaled after cleaning

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, Y, test_size=0.2, random_state=42)

    # List of models for binary classification
    models = [logreg, xgbc, rfc, knnc, dtc, svm]
    model_names = ['Logistic Regression', 'XGBoost', 'Random Forest', 'KNN', 'Decision Tree', 'SVM']

    if choice == 'best':
        final_model = None
        best_score = 0
        for m in models:
            m.fit(X_train, y_train)
            p = m.predict(X_test)
            score = accuracy_score(y_test, p)  # Use accuracy for binary classification
            if score > best_score:
                best_score = score
                final_model = m
        final_model.fit(X_train, y_train)
        p = final_model.predict(X_test)

    else:
        idx = {
            'logreg': 0,
            'xg': 1,
            'rf': 2,
            'knn': 3,
            'dt': 4,
            'svm': 5
        }.get(choice, 0)  # Default to logistic regression if choice is invalid
        m = models[idx]
        m.fit(X_train, y_train)
        p = m.predict(X_test)

    # Feature Selection via RFE (if enabled)
    if feature_selection == 'rfe':
        rfe = RFE(final_model, n_features_to_select=5)  # Select top 5 features
        X_train_rfe = rfe.fit_transform(X_train, y_train)
        X_test_rfe = rfe.transform(X_test)
        final_model.fit(X_train_rfe, y_train)
        p = final_model.predict(X_test_rfe)

    # Metrics for Binary Classification
    score = accuracy_score(y_test, p)  # Accuracy for binary classification
    print(f'Accuracy score: {score}')
    print('\n')
    print(classification_report(y_test, p))  # Precision, recall, f1-score, and support
    print('\n')

    if coef:
        return

    # Confusion Matrix
    plt.figure(figsize=(15, 8))
    sns.heatmap(confusion_matrix(y_test, p), annot=True, fmt='d', cmap='Blues', cbar=False)
    plt.title('Confusion Matrix')
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.tight_layout()
    plt.show()

    # ROC Curve and AUC for Binary Classification
    if rocc == True:
        if hasattr(final_model, "predict_proba"):  # Check if the model supports probability prediction
            y_score = final_model.predict_proba(X_test)[:, 1]
        elif hasattr(final_model, "decision_function"):  # For models like SVM
            y_score = final_model.decision_function(X_test)
        else:
            print("ROC curve cannot be generated for this model.")
            return

        fpr, tpr, _ = roc_curve(y_test, y_score)
        roc_auc = auc(fpr, tpr)

        plt.figure(figsize=(15, 8))
        plt.plot(fpr, tpr, color='blue', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
        plt.plot([0, 1], [0, 1], color='red', linestyle='--')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic (ROC) Curve')
        plt.legend(loc='lower right')
        plt.tight_layout()
        plt.show()

    # Feature Importance (if enabled)
    if feature_importance:
        # Check if model supports feature importance (works for Random Forest, XGBoost, Logistic Regression, etc.)
        if hasattr(final_model, 'feature_importances_'):
            feature_importance_values = final_model.feature_importances_
        elif hasattr(final_model, 'coef_'):
            feature_importance_values = final_model.coef_[0]  # For models like Logistic Regression
        else:
            print("Feature importance is not supported for this model.")
            return

        # Plot the feature importance
        plt.figure(figsize=(15, 8))
        sns.barplot(x=feature_importance_values, y=X.columns, palette='viridis')
        plt.title('Feature Importance')
        plt.xlabel('Importance')
        plt.ylabel('Features')
        plt.tight_layout()
        plt.show()

        # Return sorted feature importance
        a = list(zip(X.columns, feature_importance_values))
        return sorted(a, key=lambda x: x[1], reverse=True)




def reg_model(X, Y, choice='best', feature_selection='none', regularization='none'):
    # Standardize features if regularization or RFE is used
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, Y)

    models = [LinearRegression(), xgbr, rfr, knnr, dtr]
    model_names = ['Linear Regression', 'XGBoost', 'Random Forest', 'KNN', 'Decision Tree']

    if choice == 'best':
        final_model = None
        best_score = float('inf')
        for m in models:
            m.fit(X_train, y_train)
            p = m.predict(X_test)
            score = mean_squared_error(y_test, p)
            if score < best_score:
                best_score = score
                final_model = m
        final_model.fit(X_train, y_train)
        p = final_model.predict(X_test)
    else:
        idx = {
            'linear': 0,
            'xg': 1,
            'rf': 2,
            'knn': 3,
            'dt': 4,
        }.get(choice, 0)  # Default to linear regression if choice is invalid
        m = models[idx]
        m.fit(X_train, y_train)
        p = m.predict(X_test)

    # Feature Selection via RFE (if enabled)
    if feature_selection == 'rfe':
        rfe = RFE(final_model, n_features_to_select=5)  # Choose top 5 features
        X_train_rfe = rfe.fit_transform(X_train, y_train)
        X_test_rfe = rfe.transform(X_test)
        final_model.fit(X_train_rfe, y_train)
        p = final_model.predict(X_test_rfe)

    # Regularization (if enabled) using Lasso or Ridge
    if regularization == 'lasso':
        reg_model = Lasso(alpha=0.1)  # You can adjust alpha for stronger/weaker regularization
        reg_model.fit(X_train, y_train)
        p = reg_model.predict(X_test)
        final_model = reg_model  # Set final model to the regularized model
    elif regularization == 'ridge':
        reg_model = Ridge(alpha=1.0)  # You can adjust alpha for stronger/weaker regularization
        reg_model.fit(X_train, y_train)
        p = reg_model.predict(X_test)
        final_model = reg_model  # Set final model to the regularized model

    # Evaluation Metrics
    mse = mean_squared_error(y_test, p)
    mae = mean_absolute_error(y_test, p)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, p)

    print(f'Mean Squared Error (MSE): {mse:.4f}')
    print(f'Mean Absolute Error (MAE): {mae:.4f}')
    print(f'Root Mean Squared Error (RMSE): {rmse:.4f}')
    print(f'R-squared (R²): {r2:.4f}')
    print('\n')

    # Visualization: True vs Predicted
    plt.figure(figsize=(15, 8))
    plt.scatter(y_test, p, alpha=0.7, color='blue', label='Predictions')
    plt.plot([min(y_test), max(y_test)], [min(y_test), max(y_test)], color='red', linestyle='--', label='Perfect Fit')
    plt.xlabel('True Values')
    plt.ylabel('Predicted Values')
    plt.title('True vs Predicted Values')
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Residuals Distribution
    residuals = y_test - p
    plt.figure(figsize=(15, 8))
    sns.histplot(residuals, kde=True, bins=30, color='purple')
    plt.title('Residuals Distribution')
    plt.xlabel('Residuals')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.show()

    # Residuals vs Predictions
    plt.figure(figsize=(15, 8))
    plt.scatter(p, residuals, alpha=0.7, color='green')
    plt.axhline(0, color='red', linestyle='--')
    plt.title('Residuals vs Predicted Values')
    plt.xlabel('Predicted Values')
    plt.ylabel('Residuals')
    plt.tight_layout()
    plt.show()

    # Feature Importance / Coefficients
    if choice == 'best':
        chosen_model = final_model
    else:
        chosen_model = m

    plt.figure(figsize=(10, max(8, 0.5 * len(X.columns))))  # Dynamically adjust height based on feature count

    if hasattr(chosen_model, 'coef_'):  # Linear regression or regularized linear models
        coefficients = chosen_model.coef_
        feature_names = X.columns
        sorted_indices = np.argsort(np.abs(coefficients))[::-1]  # Sort by absolute value (highest to lowest)
        sorted_features = feature_names[sorted_indices]
        sorted_coefficients = coefficients[sorted_indices]

        plt.barh(sorted_features, sorted_coefficients, color='orange')
        plt.xlabel('Coefficient Value')
        plt.title(f'{model_names[models.index(chosen_model)]} Coefficients')

    elif hasattr(chosen_model, 'feature_importances_'):  # Random Forest or XGBoost
        feature_importance = chosen_model.feature_importances_
        feature_names = X.columns
        sorted_indices = np.argsort(feature_importance)[::-1]  # Sort by importance (highest to lowest)
        sorted_features = feature_names[sorted_indices]
        sorted_importance = feature_importance[sorted_indices]

        plt.barh(sorted_features, sorted_importance, color='purple')
        plt.xlabel('Feature Importance')
        plt.title(f'{model_names[models.index(chosen_model)]} Feature Importance')

    plt.tight_layout()
    plt.show()