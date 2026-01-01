from typing import Literal
import pandas as pd
import numpy as np

SEED = 42
np.random.seed(SEED)

class WindowGenerator:
    '''
    Usage:
        1) Data MUST be balanced. Same amount of time points for each unit, without gaps
        2) Time column MUST start from 1. This must be consecutive from 1,2,3.. till max time point
        3) Treatment column MUST be binary (0/1) with no nulls
    '''
    def __init__(self, 
                 dataframe: pd.DataFrame, 
                 frame_size:list,
                 unit_column:str, 
                 time_column:str,
                 treatment_column:str,
                 ):
        
        self.df = dataframe
        self.frame_size = frame_size
        self.unit_column = unit_column
        self.time_column = time_column
        self.treatment_column = treatment_column #specify that it must be 0 or 1 column with non nulls
        self.rng = np.random.default_rng(SEED)


        assert len(frame_size) == 2, "frame_size should be a tuple of (int, int)"
        for col in [unit_column, time_column, treatment_column]:
            assert col in dataframe.columns, f"{col} not found in dataframe columns"
    
    def generate_treatment_windows(self, buffer_size:tuple) -> None:
        '''
        Generate treatment windows based on frame size and buffer size.
        Steps:
            1) Generate potential windows around treatment (+/- frame_size)
            2) Check buffer conditions and filter windows
            3) Check continous time points in windows
        '''

        df_potential_windows = self._generate_windows(filter_at_value=1)
        df_buffered_windows = self._check_and_filter_buffer_windows(df=df_potential_windows, 
                                                                    buffer_size=buffer_size, 
                                                                    max_aggreements_in_buffer=1
                                                                    )
        df_treated_windows = self._check_continous_time_windows(df_buffered_windows)
        df_treated_windows = self._generate_window_t_column(df_treated_windows)
        
        self.treated_windows =  df_treated_windows.assign(is_treated_window=1).copy()
    
    def generate_control_windows(self, 
                                 buffer_size:tuple, 
                                 k:int, 
                                 t:int, 
                                 matching_method: Literal['random', 'knn'],
                                 matching_params: dict | None = None,
                                 exclude_treated_units:bool=False) -> None:
        '''
        1) Get all windows that match frame size and buffer size conditions
        2) Check buffer conditions and filter windows
        3) Check control windows continuity
        4) Match control windos with treated ones. 
            - Random Matching: For each treated window, randomly sample K control window's up to T times each
            - KNN Matching: For each treated window, find K nearest control windows based on matching_column (up to T times each)


        k: number of control windows to sample per treated window
        t: number of times a control window can be used (sampling with/without replacement) 
        exclude_treated_units: whether to exclude treated units from control windows generation

        '''
        df_potential_windows = self._generate_windows(filter_at_value=0, 
                                                      exclude_treated_units=exclude_treated_units
                                                      )
        df_buffered_windows = self._check_and_filter_buffer_windows(df=df_potential_windows, 
                                                                    buffer_size=buffer_size, 
                                                                    max_aggreements_in_buffer=0
                                                                    )
        df_control_windows = self._check_continous_time_windows(df_buffered_windows)
        df_control_windows = self._generate_window_t_column(df_control_windows)

        # Match control windows with treated windows
        if matching_method == 'random':
            if matching_params:
                print("Warning: matching_params will be ignored for random matching method.")
            df_final_control_windows = self._randomly_match_control_windows(df=df_control_windows, 
                                                                            k=k, 
                                                                            t=t)
        elif matching_method == 'knn':
            df_final_control_windows = self._knn_match_control_windows(df=df_control_windows,
                                                                      k=k, 
                                                                      t=t, 
                                                                      **matching_params
                                                                      )
        else:
            raise ValueError("Invalid matching method. Choose 'random' or 'knn'.")
        

        self.control_windows = df_final_control_windows.assign(is_treated_window=0).copy()

        self.combined_windows = pd.concat([self.treated_windows, self.control_windows], ignore_index=True)



    def _generate_windows(self, filter_at_value:int, exclude_treated_units=False) -> pd.DataFrame:
        """Generate windows of frame size + 1 (including central observation, either treatment or moment 
        zero of control)
        Also, assigns window_id to each generated window, as a combination of unit + _ + time columns.

        Args:
            filter_at_value (int): value to filter treatment column at (0 or 1)
            exclude_treated_units (bool, optional): Whether to exclude treated units from control windows generation. Defaults to False.

        Returns:
            df_windows (pd.DataFrame): DataFrame with generated windows and window_id
        """
        windows = []
        units_and_times_not_eligible = []
        #Generate all potential windows and assign a unique ID
        mask = (self.df[self.treatment_column]==filter_at_value)
        if exclude_treated_units and filter_at_value==0:
            treated_units = self.df.loc[self.df[self.treatment_column]==1, self.unit_column].unique()
            print("Excluding treated units from control windows generation:", treated_units)
            mask &=  (~self.df[self.unit_column].isin(treated_units))

        for _, row in self.df[mask].iterrows():
            unit, time = row[self.unit_column], row[self.time_column]

            # For that unit and time momwnr, get pre and post data based on frame size.
            # Between method includes the limits/bounds.
            window_mask =  ((self.df[self.unit_column]==unit) & 
                            (self.df[self.time_column].between(time - self.frame_size[0], 
                                                               time + self.frame_size[1])
                                                               )
            )
            window_data = self.df.loc[window_mask].copy()
            #Check if window_data meets frame size requirement (+1 for treatment time point)
            if len(window_data) < sum(self.frame_size) + 1:
                units_and_times_not_eligible.append(f"{unit}_{time}")
                continue
            
            window_data['window_id'] = f"{unit}_{time}"
            windows.append(window_data)
        
        if len(windows) > 0:
            df_windows = pd.concat(windows, ignore_index=True)
            print("=== Potential Windows Generation Summary ===")
            print("---> Total possible windows found:", len(self.df.loc[self.df[self.treatment_column]==filter_at_value]))
            print(f"---> Excluded {len(units_and_times_not_eligible)} units/times due to insufficient data (frame size requirement).")
            print("---> Excluded windw_id's (unit_time):", units_and_times_not_eligible) #TODO
            print(f"Generated {len(windows)} windows.")
        else:
            raise "No windows generated. Check data and frame size."
        
        return df_windows
    

    def _check_and_filter_buffer_windows(self, 
                                         df: pd.DataFrame, 
                                         buffer_size: tuple, 
                                         max_aggreements_in_buffer: int) -> pd.DataFrame:
        """Filter windows to meet buffer criteria

        Args:
            df (pd.DataFrame): dataframe with windows
            buffer_size (tuple): number of time points without intervention around time zero (pre, post).
            max_aggreements_in_buffer (int): maximum allowed treatments within buffer (1 for treated, 0 for control)  #TODO

        Returns:
            pd.DataFrame: dataframe with the windows that meet buffer criteria.
        """
        time_zero = df['window_id'].str.split('_').str[1].astype(int)
        df = df.assign(time_zero=time_zero)
        
        # Define values within buffer to check
        df['in_buffer'] = df[self.time_column].between(df['time_zero'] - buffer_size[0],
                                                       df['time_zero'] + buffer_size[1]
        )
        
        # Sum treatments within buffer per window
        buffer_sums = (df.loc[df['in_buffer']] #TODO exclude time zero? and remove max_agreements_in_buffer accordingly
                       .groupby('window_id')[self.treatment_column]
                       .sum()
        )
        valid_window_ids = buffer_sums[buffer_sums <= max_aggreements_in_buffer].index #TODO buffer_sums==0

        df_valid = df[df['window_id'].isin(valid_window_ids)].copy()

        if len(df_valid) == 0:
            raise "No valid windows after buffer checking. Adjust buffer size." 
        
        print("=== Windows Buffer Checking Summary ===")
        print(f"Generated {len(valid_window_ids)} valid windows.")

        df_valid.drop(columns=['time_zero', 'in_buffer'], inplace=True)

        return df_valid
    

    def _check_continous_time_windows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Check windows are continous in time.

        Args:
            df (pd.DataFrame): dataframe with windows that meet frame and buffer sizes. 

        Returns:
            pd.DataFrame: dataframe with windows that are continous in time.
        """
        summary = df.groupby('window_id')[self.time_column].agg(['min', 'max', 'count'])
        summary['is_continuous'] = (summary['max'] - summary['min'] + 1) == summary['count']

        valid_window_ids = summary.loc[summary['is_continuous']].index
        df_valid = df[df['window_id'].isin(valid_window_ids)].copy()

        print("=== Windows Continuity Checking Summary ===")
        print(f"Generated {len(valid_window_ids)} valid continuous windows.")
        return df_valid
    
    
    def _randomly_match_control_windows(self, df:pd.DataFrame, k:int, t:int) -> None:
        """Randomly match treated windows with control windows.
        
        1) Generate a counter for control windows usage
        2) For each treated window, randomly sample k control windows from available control windows
              (those that have been used less than t times)

        Args:
            df (pd.DataFrame): dataframe with valid control windows possible to match.
            k (int): number of control windows to sample per treated window.
            t (int): maximum number of times a control window can be used.

        Returns:
            None
        """
        #generate a dictionary of control_windows, with window_id as keys and 0 as values
        control_windows_usage = {window_id:0 for window_id in df.window_id.unique()}
        final_control_windows = []
        treated_window_id_with_controls = []
        treated_window_ids_with_no_controls = []
        for treated_window_id in self.treated_windows.window_id.unique():
            available_control_windows = [wid for wid, usage in control_windows_usage.items() if usage < t]
            #random smple k control windows from available_control_windows
            if len(available_control_windows) == 0:
                print(f"No more control windows available to sample for treated window {treated_window_id}. Skipping.")
                treated_window_ids_with_no_controls.append(treated_window_id)
                continue
            elif len(available_control_windows) < k:
                print(f"Not enough control windows available for treated window {treated_window_id}. Available: {len(available_control_windows)} less than k={k}.")
                sampled_control_windows = available_control_windows
            else:
                sampled_control_windows = self.rng.choice(available_control_windows, size=k, replace=False)
            
            for sampled_control_window_id in sampled_control_windows:
                control_windows_usage[sampled_control_window_id] += 1
                control_window_data = df[df['window_id']==sampled_control_window_id].copy()
                control_window_data['matched_treated_window_id'] = treated_window_id
                final_control_windows.append(control_window_data)
            treated_window_id_with_controls.append(treated_window_id)

        if len(final_control_windows) > 0:
            print(f"Treated windows with matched controls: {len(treated_window_id_with_controls)}")
            print(f"Treated windows with NO matched controls: {len(treated_window_ids_with_no_controls)}. Drop from treated dataset.")
            self.treated_windows = self.treated_windows[~self.treated_windows['window_id'].isin(treated_window_ids_with_no_controls)].copy()
            return pd.concat(final_control_windows, ignore_index=True)
        else:
            raise "No control windows matched. Check parameters k and t."
    
    def _knn_match_control_windows(self, 
                                   df:pd.DataFrame, 
                                   k:int, 
                                   t:int, 
                                   matching_columns:list[str],
                                   distance_threshold:float) -> None:
        """KNN match treated windows with control windows based on matching_column.
        
        1) Generate a counter for control windows usage
        2) For each treated window, find k nearest control windows based on matching_column
              (those that have been used less than t times)

        Args:
            df (pd.DataFrame): dataframe with valid control windows possible to match.
            k (int): number of control windows to sample per treated window.
            t (int): maximum number of times a control window can be used.

        Returns:
            None
        """

        '''
        DONE Generate empty counter
        DONE check matching column has no nans
        1) Iterar por cada treated window
            DONE - filtrar por los controles available
            - computar distancias noramlizadas en matching column entre momento 0 de treated y los controles
            - filtrar por las distancias menores o iguales a distance_knn (threshold)
            - quedarse con los k controles mas cercanos dentro 
            - actualizar el contador
            - asignar matched_treated_window_id
        2) Concatenar todos los controles seleccionados
        3) Devolver dataframe de controles
        4) Manejar casos en los que no hay controles disponibles o no hay controles dentro
        
        '''
        # Check missing values in matching column
        control_windows_with_missing_matching_col = df.loc[(df['window_t']==0) & (df[matching_columns].isna().any(axis=1)), 'window_id'].unique().tolist()
        if len(control_windows_with_missing_matching_col) > 0:
            print(f"Warning: The following control windows have missing values in some matching columns '{matching_columns}' and will be excluded from matching: {len(control_windows_with_missing_matching_col)}")
            df = df[~df['window_id'].isin(control_windows_with_missing_matching_col)].copy()   
        
        treated_windows_with_missing_matching_col = self.treated_windows.loc[(self.treated_windows['window_t']==0) & (self.treated_windows[matching_columns].isna().any(axis=1)), 'window_id'].unique().tolist()
        if len(treated_windows_with_missing_matching_col) > 0:
            print(f"Warning: The following treated windows have missing values in some matching columns '{matching_columns}' and will be excluded from matching: {len(treated_windows_with_missing_matching_col)}")
            self.treated_windows = self.treated_windows[~self.treated_windows['window_id'].isin(treated_windows_with_missing_matching_col)].copy()

        #Generate matching_columns normalized 
        for col in matching_columns:
            col_min = min(df[col].min(), self.treated_windows[col].min())
            col_max = max(df[col].max(), self.treated_windows[col].max())
            df[f'{col}_norm'] = (df[col] - col_min) / (col_max - col_min)
            self.treated_windows[f'{col}_norm'] = (self.treated_windows[col] - col_min) / (col_max - col_min)

        matching_columns_norm = [f'{col}_norm' for col in matching_columns]
        
        # Generate empty counter
        control_windows_usage = {window_id:0 for window_id in df.window_id.unique()}
        final_control_windows = []
        treated_window_id_with_controls = []
        treated_window_ids_with_no_controls = []
        for treated_window_id in self.treated_windows.window_id.unique():
            available_control_windows = [wid for wid, usage in control_windows_usage.items() if usage < t]
            if len(available_control_windows) == 0:
                print(f"No more control windows available to sample for treated window {treated_window_id}. Skipping.")
                treated_window_ids_with_no_controls.append(treated_window_id)
                continue

            possible_controls_match_col_values = (df.loc[(df['window_id'].isin(available_control_windows)) &
                                                (df['window_t']==0), 
                                                ["window_id"] + matching_columns_norm].copy()
            )
            treated_match_col_values = (self.treated_windows.loc[(self.treated_windows['window_id']==treated_window_id) &
                                                        (self.treated_windows['window_t']==0), 
                                                        matching_columns_norm].values)

            #Compute the normalized euclidean distance between treated and control windows
            possible_controls_match_col_values['norm_distance'] = self._compute_normalized_euclidean_distance(
                controls_matching_vals=possible_controls_match_col_values[matching_columns_norm].values,
                treated_matching_vals=treated_match_col_values,
                nbr_matching_cols=len(matching_columns_norm)
            )
            #Filter by distance threshold
            possible_controls_match_col_values = possible_controls_match_col_values[
                possible_controls_match_col_values['norm_distance'] <= distance_threshold
            ]
            if len(possible_controls_match_col_values) == 0:
                print(f"No control windows within distance threshold for treated window {treated_window_id}. Skipping.")
                treated_window_ids_with_no_controls.append(treated_window_id)
                continue
            #Get k nearest control windows
            possible_controls_match_col_values = possible_controls_match_col_values.sort_values('norm_distance')
            if len(possible_controls_match_col_values) < k:
                print(f"Not enough control windows within distance threshold for treated window {treated_window_id}. Available: {len(possible_controls_match_col_values)} less than k={k}.")
                selected_control_window_ids = possible_controls_match_col_values['window_id'].values
            else:
                selected_control_window_ids = possible_controls_match_col_values['window_id'].values[:k]
            
            for selected_control_window_id in selected_control_window_ids:
                control_windows_usage[selected_control_window_id] += 1
                control_window_data = df[df['window_id']==selected_control_window_id].copy()
                control_window_data['matched_treated_window_id'] = treated_window_id
                final_control_windows.append(control_window_data)
            treated_window_id_with_controls.append(treated_window_id)

        if len(final_control_windows) == 0:
            raise "No control windows matched. Check parameters k, t, and distance_threshold."
        
        print(f"Treated windows with matched controls: {len(treated_window_id_with_controls)}")
        print(f"Treated windows with NO matched controls: {len(treated_window_ids_with_no_controls)}. Drop from treated dataset.")
        self.treated_windows = self.treated_windows[~self.treated_windows['window_id'].isin(treated_window_ids_with_no_controls)].copy()
        #Drop normalized columns from df
        df.drop(columns=matching_columns_norm, inplace=True)
        self.treated_windows.drop(columns=matching_columns_norm, inplace=True)
        return pd.concat(final_control_windows, ignore_index=True)

    
    def _generate_window_t_column(self, df:pd.DataFrame) -> pd.DataFrame:
        """Generate window_t column indicating time relative to treatment/moment zero.

        Args:
            df (pd.DataFrame): dataframe with windows.

        Returns:
            pd.DataFrame: dataframe with window_t column added.
        """
        time_zero = df['window_id'].str.split('_').str[1].astype(int)
        df = df.assign(time_zero=time_zero)
        df['window_t'] = df[self.time_column] - df['time_zero']
        df.drop(columns=['time_zero'], inplace=True)
        return df
    

    @staticmethod
    def _compute_normalized_euclidean_distance(controls_matching_vals:np.ndarray, 
                                               treated_matching_vals:np.ndarray, 
                                               nbr_matching_cols:int) -> np.ndarray:
        """Compute normalized Euclidean distance between control windows and treated window.
        Args:
            controls_matching_vals (np.ndarray): array of shape (n_controls, n_matching_columns) with matching columns values for control windows.
            treated_matching_vals (np.ndarray): array of shape (n_matching_columns,) with matching columns values for treated window.
            nbr_matching_cols (int): number of matching columns.
        Returns:
            np.ndarray: array of shape (n_controls,) with normalized Euclidean distances.
        """
        normalized_distances = np.linalg.norm(controls_matching_vals - treated_matching_vals, axis=1) / np.sqrt(nbr_matching_cols)
        return normalized_distances