import os
import numpy as np
import pandas as pd
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from catboost import Pool
from catboost import CatBoostClassifier
import scipy.io.wavfile as wavfile
import python_speech_features.base as speech

class pohui:
    def __init__(self):
        if not os.path.exists('data/ours.csv'):
            raise Exception("No base data to train on (data/ours.csv missing)")
        if not os.path.exists('data/random.csv'):
            raise Exception("No base data to train on (data/random.csv missing)")
        ourdata = pd.read_csv('data/ours.csv')
        ourdata = ourdata.sample(frac=1)
        randoms = pd.read_csv('data/random.csv')
        self.upd = pd.concat([randoms, ourdata], ignore_index = True).sample(frac = 1)
        if not os.path.exists('models'):
            os.makedirs('models')
            trainModels()
        else:
            self.cbc0 = CatBoostClassifier()
            self.cbc1 = CatBoostClassifier()
            self.cbc2 = CatBoostClassifier()
            self.cbc3 = CatBoostClassifier()
            self.cbc4 = CatBoostClassifier()
            try:
                self.cbc0.load_model('models/cbc0.cbm')
                self.cbc1.load_model('models/cbc1.cbm')
                self.cbc2.load_model('models/cbc2.cbm')
                self.cbc3.load_model('models/cbc3.cbm')
                self.cbc4.load_model('models/cbc4.cbm')
            except:
                trainModels()
                saveModels()

    def saveModels():
        self.cbc0.save_model('models/cbc0.cbm')
        self.cbc1.save_model('models/cbc1.cbm')
        self.cbc2.save_model('models/cbc2.cbm')
        self.cbc3.save_model('models/cbc3.cbm')
        self.cbc4.save_model('models/cbc4.cbm')

    def Features(data, rate, dim):
        spec = np.abs(np.fft.rfft(data))
        freq = np.fft.rfftfreq(len(data), d=1 / dim)
        a = spec / spec.sum()
        meaN = (freq * a).sum()
        std = np.sqrt(np.sum(a * ((freq - meaN) ** 2)))
        a_cumsum = np.cumsum(a)
        mediaN = freq[len(a_cumsum[a_cumsum <= 0.5])]
        modE = freq[a.argmax()]
        q25 = freq[len(a_cumsum[a_cumsum <= 0.25])]
        q75 = freq[len(a_cumsum[a_cumsum <= 0.75])]
        IQR = q75 - q25
        z = a - a.mean()
        w = a.std()
        skewnesS = ((z ** 3).sum() / (len(spec) - 1)) / w ** 3
        kurtosiS = ((z ** 4).sum() / (len(spec) - 1)) / w ** 4
    
        m = speech.mfcc(data,rate)
        f = speech.fbank(data,rate)
        l = speech.logfbank(data,rate)
        s = speech.ssc(data,rate)
    
        data = pd.DataFrame(data)
        desc = data.describe()
        mean = desc.loc["mean"].get(0)
        mad = data.mad().get(0)
        sd = desc.loc["std"].get(0)
        median = data.median().get(0)
        minimum = desc.loc["min"].get(0)
        maximum = desc.loc["max"].get(0)
        Q25 = desc.loc["25%"].get(0)
        Q75 = desc.loc["75%"].get(0)
        interquartileR = Q75 - Q25
        skewness = data.skew().get(0)
        kurtosis = data.kurtosis().get(0)
    
        result = {
            "Mean": mean, "Mad": mad, "deviation": sd, "Median": median, "Min": minimum, "Max": maximum, 
            "interquartileR": interquartileR, "Skewness": skewness, "Q25": Q25, "Q75": Q75, "Kurtosis": kurtosis,
            "mfcc_mean": np.mean(m), "mfcc_max": np.max(m), "mfcc_min": np.min(m),
            "fbank_mean": np.mean(f[0]), "fbank_max": np.max(f[0]), "fbank_min": np.min(f[0]),
            "energy_mean": np.mean(f[1]), "energy_max": np.max(f[1]), "energy_min": np.min(f[1]),
            "lfbank_mean": np.mean(l), "lfbank_max": np.max(l), "lfbank_min": np.min(l),
            "ssc_mean": np.mean(s), "ssc_max": np.max(s), "ssc_min": np.min(s),
            "meaN": meaN, "deviatioN": std, "mediaN": mediaN, "modE": modE, "IQR": IQR,
            "skewnesS": skewnesS, "q25": q25, "q75": q75, "kurtosiS": kurtosiS}

        return result
    
    def StereoToMono(data):
        newdata = []
        for i in range(len(data)):
            d = (data[i][0] + data[i][1])/2
            newdata.append(d)
        return(np.array(newdata, dtype='int16'))
    
    def trainModels():
        x = self.upd.drop(columns = ["person"]).values
        y = self.upd["person"].values
        x_train, x_valid, y_train, y_valid = train_test_split(x, y, test_size=0.42)
        le = preprocessing.LabelEncoder()
        le.fit(list(upd.person.unique()))
        y_train = le.transform(y_train)
        y_valid = le.transform(y_valid)

        train = Pool(x_train, y_train)
        valid = Pool(x_valid, y_valid)

        self.cbc0 = CatBoostClassifier(iterations=100, learning_rate=0.01, depth=5)
        self.cbc0.fit(train, eval_set=valid, use_best_model=True, verbose=False)
        self.cbc1 = CatBoostClassifier(iterations=100, learning_rate=0.001, depth=4)
        self.cbc1.fit(train, eval_set=valid, use_best_model=True, verbose=False)
        self.cbc2 = CatBoostClassifier(iterations=100, learning_rate=0.0001, depth=3)
        self.cbc2.fit(train, eval_set=valid, use_best_model=True, verbose=False)
        self.cbc3 = CatBoostClassifier(iterations=100, learning_rate=0.00001, depth=2)
        self.cbc3.fit(train, eval_set=valid, use_best_model=True, verbose=False)
        self.cbc4 = CatBoostClassifier(iterations=100, learning_rate=0.000001, depth=1)
        self.cbc4.fit(train, eval_set=valid, use_best_model=True, verbose=False)

        saveModels()

    def registerUser(self, name, age, gender, pathToWav):
        if not os.path.exists(pathToWav):
            raise Exception('No such file exists (can\'t register user)')

        if gender not in [0, 1]:
            raise Exception('Invalid gender entered')

        if age >= 0 and age < 25:
            age = 20
        elif age >= 25 and age < 35:
            age = 30
        elif age >= 35 and age < 45:
            age = 40
        elif age >= 45 and age < 101:
            age = 50
        else:
            raise Exception('Invalid age entered')

        rate, newdata = wavfile.read(pathToWav)

        try:
            newdata = StereoToMono(newdata)
        except:
            pass

        chunk_size = len(newdata)//5
        for start in range(0, len(newdata), len(newdata)//10):
            temp = []
            temp.append(gender)
            temp.append(age)
            f = Features(newdata[start:start+chunk_size],rate,1000)
            for feature in f:
                temp.append(f[feature])
            temp.append(name)
            if temp[6]!=0 and 'nan' not in ','.join(list(map(str,temp))):
                self.upd = upd.reset_index(drop=True)
                self.upd.loc[upd.shape[0]] = temp

        t = open("data/ours.csv",'r').read()
        open("data/ours.csv",'w').write(t+'\n'+','.join(list(map(str,temp))))
    
        self.upd = self.upd.sample(frac=1)

        self.trainModels()

    def predict(self, age, gender, pathToWav):
        if not os.path.exists(pathToWav):
            raise Exception('No such file exists (can\'t predict)')
        # do smth

    def getRegistered(self):
        ourdata = pd.read_csv('data/ours.csv')
        registered = ourdata[['person', 'age', 'gender']].drop_duplicates(subset=['person']).rename(columns={'person':'name', 'age':'age', 'gender':'gender'})
        return registered.to_json()