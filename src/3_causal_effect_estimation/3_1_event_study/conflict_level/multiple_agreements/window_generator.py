import numpy as np
import pandas as pd

np.random.seed(42)

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
        # self.matching_column

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
    
    def generate_control_windows_random_matching(self, buffer_size:tuple, k:int, t:int, exclude_treated_units:bool=False) -> None:
        '''
        1) Get all windows that match frame size and buffer size conditions
        2) Check buffer conditions and filter windows
        3) Check control windows continuity
        4) For each treated window, randomly sample K control window's up to T times each

        k: number of control windows to sample per treated window
        t: number of times to sample k control windows per treated window
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
        df_final_control_windows = self._randomly_match_control_windows(df=df_control_windows, k=k, t=t)
        df_final_control_windows = self._generate_window_t_column(df_final_control_windows)

        self.control_windows = df_final_control_windows.assign(is_treated_window=0).copy()

        self.combined_windows = pd.concat([self.treated_windows, self.control_windows], ignore_index=True)


        # window_t


    def _generate_windows(self, filter_at_value:int, exclude_treated_units=False) -> None:
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
            print("---> Excluded windw_id's (unit_time):", units_and_times_not_eligible)
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
            df (pd.DataFrame): dataframe with windows of frame size
            buffer_size (tuple): size of buffer before and after treatment/moment zero (int, int).
            max_aggreements_in_buffer (int): maximum allowed treatments within buffer (1 for treated, 0 for control)

        Returns:
            pd.DataFrame: dataframe with windows that meet buffer criteria.
        """
        time_zero = df['window_id'].str.split('_').str[1].astype(int)
        df = df.assign(time_zero=time_zero)
        
        # Define values within buffer to check
        df['in_buffer'] = df[self.time_column].between(df['time_zero'] - buffer_size[0],
                                                       df['time_zero'] + buffer_size[1]
        )
        
        # Sum treatments within buffer per window
        buffer_sums = (df.loc[df['in_buffer']]
                       .groupby('window_id')[self.treatment_column]
                       .sum()
        )
        valid_window_ids = buffer_sums[buffer_sums <= max_aggreements_in_buffer].index

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
            pd.DataFrame: _description_
        """
        summary = df.groupby('window_id')[self.time_column].agg(['min', 'max', 'count'])
        summary['is_continuous'] = (summary['max'] - summary['min'] + 1) == summary['count']

        valid_ids = summary.loc[summary['is_continuous']].index
        df_valid = df[df['window_id'].isin(valid_ids)].copy()

        print("=== Windows Continuity Checking Summary ===")
        print(f"Generated {len(valid_ids)} valid continuous windows.")

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
        #generate a dictionary with control_windows window_id as keys and a 0 as values
        control_windows_usage = dict.fromkeys(df.window_id.unique(), 0)
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
                print(f"Not enough control windows available to sample {k} for treated window {treated_window_id}. Available: {len(available_control_windows)}")
                sampled_control_windows = available_control_windows
            else:
                sampled_control_windows = np.random.choice(available_control_windows, size=k, replace=False)
            
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