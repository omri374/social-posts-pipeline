import os
import time
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import pandas as pd
MIN_SAMPLES_PER_CATEGORY = 5


class AbstractTrendDetector(ABC):

    @abstractmethod
    def __init__(self, freq, is_multicategory=False, resample=True):

        """Abstract class for single and multi-category time series anomaly detection

        Parameters
        ----------
        is_multicategory: bool
            Specifies whether the data is held with a pandas MultiIndex, where the first index is date/time and the
            second is a category. This is used for multiple time series, one for each category

        """

        self.is_multicategory = is_multicategory
        self.freq = freq
        self.resample = resample
        self.input_data = {}

    @abstractmethod
    def fit_one_category(self, dataset, category=None, verbose=False):
        pass

    def fit(self, X, y=None, verbose=False):
        """Fits the trend detection.

        Parameters
        ----------
        dataset : pandas.DataFrame
            A pandas DataFrame with either:
            * a two-leveled multi-index, the first indexing time and the second indexing class/topic frequency
            per-window, and a single column of a numeric dtype
            * a DatetimeIndex, and a value column of a numeric dtype

        """

        # Check that X and y have correct shape

        if y is not None:
            print("Ignoring value y, this model is unsupervised")

        if self.is_multicategory:
            X = X.reset_index()
            X = X.set_index('date')

        if 'category' not in X:
            return self.fit_one_category(X, category=self.GENERAL_CATEGORY, verbose=verbose)

        categories = X['category'].unique()
        for category in categories:
            one_category = X.loc[X['category'] == category,]

            one_category = one_category.resample(self.freq, convention='start').asfreq().fillna(0)
            one_category['category'] = category
            one_category = one_category.resample(self.freq, convention='start').asfreq().fillna(0)
            if len(one_category) < MIN_SAMPLES_PER_CATEGORY:
                continue
            # one_category = one_category.asfreq(freq = self.freq)
            self.fit_one_category(one_category, category=category, verbose=verbose)

    @abstractmethod
    def predict_one_category(self, X, category):
        pass

    def predict(self, X, plot=False, verbose=False):
        output = pd.DataFrame()

        if self.is_multicategory:
            X = X.reset_index()

        if 'category' not in X:
            self.fit_one_category(X,category=self.GENERAL_CATEGORY)
            return self.predict_one_category(X,category=self.GENERAL_CATEGORY)

        categories = X['category'].unique()

        if verbose:
            print("categories found = {}".format(categories))
        category_count = 0
        for category in categories:
            print(category)
            one_category = self.get_one_category_df(X, category)

            res = self.predict_one_category(one_category, category)
            res['category'] = category
            output = pd.concat([output, res])

        if self.is_multicategory:
            output = output.reset_index().set_index(['date', 'category'])

        return output

    def get_one_category_df(self, X, category):
        one_category = X.loc[X['category'] == category,]
        one_category['date'] = pd.DatetimeIndex(one_category['date'])
        one_category = one_category.set_index('date')
        if self.resample:
            one_category = one_category[~one_category.index.duplicated(keep='first')]
            one_category = one_category.resample(self.freq, convention='start').asfreq().fillna(0)
        return one_category

    def _type(self):
        return self.__class__.__name__

    def plot(self, labels=None,postfix = ""):
        import path

        if self.input_data is None:
            print("No data found")

        if len(self.input_data.keys()) == 1:
            self.plot_one_category(self.GENERAL_CATEGORY)
        else:
            categories = self.input_data.keys()

            category_count = 0
            for category in categories:
                if labels is not None:
                    if(isinstance(labels.index,pd.MultiIndex)):
                        labels = labels.reset_index().set_index('date')
                    category_label = labels.loc[labels['category'] == category,]
                    category_label = category_label.drop(labels = "category",axis = 1)
                else:
                    category_label = None

                plt.clf()
                plt.figure(category_count,figsize=(20,10))
                self.plot_one_category(category=category, labels=category_label)
                strFile = "../plots/"+self._type() + "-" + str(postfix) + "-" + category + ".png"
                if os.path.isfile(strFile):
                    os.remove(strFile)
                plt.savefig(strFile)
