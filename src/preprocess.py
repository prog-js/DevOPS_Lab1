# После выполнения скрипта в папке data/ появятся файлы:
# data/
# ├── X_train.csv
# ├── X_val.csv
# ├── X_test.csv
# ├── y_train.csv
# ├── y_val.csv
# ├── y_test.csv
# └── data_graduates_university_specialty_124_v20250709.csv (исходный)


import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

class GraduateSpecialtyPreprocessor:
    """
    Предобработка данных о выпускниках с разбивкой по направлениям подготовки
    Целевая переменная: average_salary_fact_avg (средняя зарплата)
    """
    
    def __init__(self, config=None):
        self.config = config
        self.label_encoders = {}
        self.scaler = StandardScaler()
        
    def load_data(self, path = os.path.join('data', 'data_graduates_university_124_v20250709_csv', 'data_graduates_university_specialty_124_v20250709.csv')):
        """Загрузка данных из CSV"""
        print(f"Загрузка данных из {path}...")
        df = pd.read_csv(path, low_memory=False, sep=';')
        print(f"Загружено строк: {len(df)}")
        print(f"Колонок: {len(df.columns)}")
        return df
    
    def fill_salary_missing_by_group(self, df, salary_col):
        """
        Заполнение пропусков в зарплате медианой по группе:
        регион (object_name) + учебное заведение (university) + направление подготовки (specialty)
        """
        group_cols = ['object_name', 'university', 'specialty']
        
        # Рассчитываем медиану по группе
        df['median_by_group'] = df.groupby(group_cols)[salary_col].transform(
            lambda x: x.median()
        )
        
        # Заполняем пропуски медианой группы
        filled_count = df[salary_col].isna().sum()
        df[salary_col] = df[salary_col].fillna(df['median_by_group'])
        
        # Если после групповой медианы остались пропуски -> заполняем общей медианой
        remaining_nulls = df[salary_col].isna().sum()
        if remaining_nulls > 0:
            global_median = df[salary_col].median()
            df[salary_col] = df[salary_col].fillna(global_median)
            print(f"  - {salary_col}: {filled_count} пропусков заполнено медианой группы, "
                  f"ещё {remaining_nulls} - глобальной медианой")
        else:
            print(f"  - {salary_col}: {filled_count} пропусков заполнено медианой группы")
        
        # Удаляем временный столбец
        df.drop('median_by_group', axis=1, inplace=True)
        
        return df
    
    def preprocess(self, df, target_col='average_salary_fact_avg'):
        """
        Полный цикл предобработки данных
        """
        print("\n--- Начало предобработки ---")
        original_shape = df.shape
        
        # 1. Удаление бесполезных столбцов (ОКТМО, ОКАТО и другие идентификаторы)
        cols_to_drop = ['oktmo', 'okato']
        existing_drop = [c for c in cols_to_drop if c in df.columns]
        if existing_drop:
            df = df.drop(columns=existing_drop)
            print(f"Удалены столбцы: {existing_drop}")
        
        # 2. Удаление явных дубликатов
        df = df.drop_duplicates()
        print(f"Удалено дубликатов: {original_shape[0] - df.shape[0]}")
        
        # 3. Заполнение пропусков в зарплатах
        salary_cols = ['average_salary_fact_avg', 'average_salary_fact_med',
                       'average_salary_norm_avg', 'average_salary_norm_med']
        
        for col in salary_cols:
            if col in df.columns:
                print(f"\nОбработка пропусков в {col}:")
                null_count = df[col].isna().sum()
                print(f"  - Пропусков до заполнения: {null_count} ({null_count/len(df)*100:.2f}%)")
                df = self.fill_salary_missing_by_group(df, col)
        
        # 4. Обработка пропусков в других колонках
        # percent_combine_work_and_study
        if 'percent_combine_work_and_study' in df.columns:
            df['percent_combine_work_and_study'] = df.groupby(
                ['object_name', 'university', 'specialty']
            )['percent_combine_work_and_study'].transform(
                lambda x: x.fillna(x.median())
            )
            df['percent_combine_work_and_study'] = df['percent_combine_work_and_study'].fillna(0)
        
        # 5. Создание новых признаков (feature engineering)
        if 'year' in df.columns:
            df['years_since_graduation'] = 2024 - df['year']
            print(f"Создан признак years_since_graduation")
        
        # 6. Удаление выбросов по целевой переменной (если она есть в данных)
        if target_col in df.columns:
            # Удаляем строки, где зарплата = 0 или отрицательная
            df = df[df[target_col] > 0]
            
            # Удаление выбросов по методу IQR или 3 сигм
            mean_val = df[target_col].mean()
            std_val = df[target_col].std()
            lower_bound = max(0, mean_val - 3 * std_val)
            upper_bound = mean_val + 3 * std_val
            outliers_before = df.shape[0]
            df = df[(df[target_col] >= lower_bound) & (df[target_col] <= upper_bound)]
            print(f"Удалено выбросов по целевой переменной: {outliers_before - df.shape[0]}")
        
        # 7. Кодирование категориальных признаков
        categorical_cols = ['object_level', 'object_name', 'gender', 
                           'education_level', 'university', 
                           'specialty_section', 'specialty']
        
        existing_cat = [c for c in categorical_cols if c in df.columns]
        print(f"\nКодирование категориальных признаков: {existing_cat}")
        
        for col in existing_cat:
            le = LabelEncoder()
            # Преобразуем в строку для избежания ошибок
            df[col] = df[col].astype(str)
            df[col] = le.fit_transform(df[col])
            self.label_encoders[col] = le
            print(f"  - {col}: {len(le.classes_)} уникальных значений")
        
        print(f"\nРазмер данных после предобработки: {df.shape}")
        print("--- Предобработка завершена ---")
        
        return df
    
    def split_and_save(self, df, target_col='average_salary_fact_avg'):
        """
        Разделение данных на train/val/test и сохранение
        """
        print("\n--- Разделение данных ---")
        
        if target_col not in df.columns:
            raise ValueError(f"Целевая колонка {target_col} не найдена в данных!")
        
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        print(f"Признаки X: {X.shape}")
        print(f"Целевая y: {y.shape}")
        
        # Train/Val/Test: 70/15/15
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=None
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.5, random_state=42
        )
        
        print(f"Train: {len(X_train)} ({len(X_train)/len(X)*100:.1f}%)")
        print(f"Val: {len(X_val)} ({len(X_val)/len(X)*100:.1f}%)")
        print(f"Test: {len(X_test)} ({len(X_test)/len(X)*100:.1f}%)")
        
        # Масштабирование числовых признаков
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        print(f"\nМасштабирование числовых признаков: {len(numeric_cols)} колонок")
        
        X_train_scaled = self.scaler.fit_transform(X_train[numeric_cols])
        X_val_scaled = self.scaler.transform(X_val[numeric_cols])
        X_test_scaled = self.scaler.transform(X_test[numeric_cols])
        
        # Сохранение данных в папку data/
        os.makedirs('data', exist_ok=True)
        
        pd.DataFrame(X_train_scaled, columns=numeric_cols).to_csv('data/X_train.csv', index=False)
        pd.DataFrame(X_val_scaled, columns=numeric_cols).to_csv('data/X_val.csv', index=False)
        pd.DataFrame(X_test_scaled, columns=numeric_cols).to_csv('data/X_test.csv', index=False)
        
        y_train.to_csv('data/y_train.csv', index=False, header=[target_col])
        y_val.to_csv('data/y_val.csv', index=False, header=[target_col])
        y_test.to_csv('data/y_test.csv', index=False, header=[target_col])
        
        # Сохранение трансформеров
        os.makedirs('models', exist_ok=True)
        
        with open('models/scaler.pkl', 'wb') as f:
            pickle.dump(self.scaler, f)
        
        with open('models/label_encoders.pkl', 'wb') as f:
            pickle.dump(self.label_encoders, f)
        
        # Сохранить список числовых колонок (понадобится для API)
        with open('models/numeric_columns.pkl', 'wb') as f:
            pickle.dump(numeric_cols, f)
        
        print("\n--- Данные сохранены ---")
        print(f"  X_train: data/X_train.csv")
        print(f"  X_val: data/X_val.csv")
        print(f"  X_test: data/X_test.csv")
        print(f"  y_train: data/y_train.csv")
        print(f"  y_val: data/y_val.csv")
        print(f"  y_test: data/y_test.csv")
        print(f"  scaler: models/scaler.pkl")
        print(f"  label_encoders: models/label_encoders.pkl")
        
        return X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test


if __name__ == '__main__':
    # Инициализация и запуск
    processor = GraduateSpecialtyPreprocessor()
    
    # Загрузка данных (укажите корректный путь к вашему CSV)
    df = processor.load_data(os.path.join('data', 'data_graduates_university_124_v20250709_csv', 'data_graduates_university_specialty_124_v20250709.csv'))
    
    # Предобработка
    df_processed = processor.preprocess(df, target_col='average_salary_fact_avg')
    
    # Разделение и сохранение
    processor.split_and_save(df_processed, target_col='average_salary_fact_avg')
    
    print("\n✅ Готово! Данные предобработаны и сохранены.")