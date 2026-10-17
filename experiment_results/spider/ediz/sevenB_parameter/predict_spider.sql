SELECT COUNT(DISTINCT Singer_ID) FROM singer
SELECT COUNT(DISTINCT Singer_ID) AS Total_Singers FROM singer
SELECT Name, Country, Age FROM singer ORDER BY Age DESC
SELECT Name, Country, Age FROM singer ORDER BY Age DESC
SELECT AVG(Age) AS AverageAge, MIN(Age) AS MinimumAge, MAX(Age) AS MaximumAge FROM singer WHERE Country = 'France'
SELECT AVG(Age) AS AverageAge, MIN(Age) AS MinimumAge, MAX(Age) AS MaximumAge FROM singer WHERE Country = 'France'
SELECT Song_Name, Song_release_year FROM singer WHERE Age = (SELECT MIN(Age) FROM singer)
SELECT Song_Name, Song_release_year FROM singer WHERE Age = (SELECT MIN(Age) FROM singer)
SELECT DISTINCT Country FROM singer WHERE Age > 20
SELECT DISTINCT Country FROM singer WHERE Age > 20
SELECT Country , COUNT(*) FROM singer GROUP BY Country
SELECT Country, COUNT(*) FROM singer GROUP BY Country
SELECT Song_Name FROM singer WHERE Age > (SELECT AVG(Age) FROM singer)
SELECT Song_Name FROM singer WHERE Age > (SELECT AVG(Age) FROM singer)
SELECT Location, Name FROM stadium WHERE Capacity BETWEEN 5000 AND 10000
SELECT Location, Name FROM stadium WHERE Capacity BETWEEN 5000 AND 10000
SELECT MAX(Capacity) AS Max_Capacity, AVG(Capacity) AS Avg_Capacity FROM stadium
SELECT AVG(Capacity) AS Average_Capacity, MAX(Capacity) AS Maximum_Capacity FROM stadium
SELECT Name, Capacity FROM stadium WHERE Average = (SELECT MAX(Average) FROM stadium)
SELECT Name, Capacity FROM stadium WHERE Average = (SELECT MAX(Average) FROM stadium)
SELECT COUNT(*) FROM concert WHERE Year IN ('2014', '2015')
SELECT COUNT(*) FROM concert WHERE Year = '2014' OR Year = '2015'
SELECT s.Name, COUNT(c.concert_ID) AS Number_of_Concerts FROM stadium s JOIN concert c ON s.Stadium_ID = c.Stadium_ID GROUP BY s.Stadium_ID, s.Name
SELECT Stadium_ID, COUNT(concert_ID) FROM concert INNER JOIN singer_in_concert ON concert.concert_ID = singer_in_concert.concert_ID GROUP BY Stadium_ID
SELECT s.Name, s.Capacity FROM stadium s JOIN concert c ON s.Stadium_ID = c.Stadium_ID JOIN singer_in_concert sic ON c.concert_ID = sic.concert_ID WHERE c.Year >= 2014 GROUP BY s.Stadium_ID ORDER BY COUNT(c.concert_ID) DESC LIMIT 1
SELECT s.Name, s.Capacity FROM stadium s JOIN concert c ON s.Stadium_ID = c.Stadium_ID WHERE c.Year > 2013 GROUP BY s.Stadium_ID ORDER BY COUNT(c.concert_ID) DESC LIMIT 1
SELECT Year FROM concert GROUP BY Year ORDER BY COUNT(*) DESC LIMIT 1
SELECT Year FROM concert GROUP BY Year ORDER BY COUNT(*) DESC LIMIT 1
SELECT Name FROM stadium WHERE Stadium_ID NOT IN (SELECT Stadium_ID FROM concert)
SELECT Name FROM stadium WHERE Stadium_ID NOT IN (SELECT Stadium_ID FROM concert)
SELECT DISTINCT Country FROM singer WHERE Age > 40 INTERSECT SELECT DISTINCT Country FROM singer WHERE Age < 30
SELECT Name FROM stadium WHERE Stadium_ID NOT IN (SELECT Stadium_ID FROM concert WHERE Year = '2014')
SELECT Name FROM stadium WHERE Stadium_ID NOT IN (SELECT Stadium_ID FROM concert WHERE Year = '2014')
SELECT c.concert_Name, c.Theme, COUNT(sc.Singer_ID) AS Number_of_Singers FROM concert c JOIN singer_in_concert sc ON c.concert_ID = sc.concert_ID GROUP BY c.concert_ID, c.concert_Name, c.Theme
SELECT concert_Name, Theme, COUNT(Singer_ID) AS Number_of_Singers FROM concert JOIN singer_in_concert ON concert.concert_ID = singer_in_concert.concert_ID GROUP BY concert_Name, Theme
SELECT T2.Name, COUNT(T1.concert_ID) FROM singer_in_concert AS T1 JOIN singer AS T2 ON T1.Singer_ID = T2.Singer_ID GROUP BY T2.Name
SELECT s.Name, COUNT(sc.concert_ID) FROM singer s JOIN singer_in_concert sc ON s.Singer_ID = sc.Singer_ID GROUP BY s.Name
SELECT DISTINCT s.Name FROM singer s JOIN singer_in_concert sic ON s.Singer_ID = sic.Singer_ID JOIN concert c ON sic.concert_ID = c.concert_ID WHERE c.Year = '2014'
SELECT DISTINCT s.Name FROM singer s JOIN singer_in_concert sic ON s.Singer_ID = sic.Singer_ID JOIN concert c ON sic.concert_ID = c.concert_ID WHERE c.Year = '2014'
SELECT Name, Country FROM singer WHERE Song_Name LIKE '%Hey%'
SELECT Name, Country FROM singer WHERE Song_Name LIKE '%Hey%'
SELECT s.Name, s.Location FROM stadium s JOIN concert c ON s.Stadium_ID = c.Stadium_ID WHERE c.Year = '2014' INTERSECT SELECT s.Name, s.Location FROM stadium s JOIN concert c ON s.Stadium_ID = c.Stadium_ID WHERE c.Year = '2015'
SELECT s.Name, s.Location FROM stadium s JOIN concert c ON s.Stadium_ID = c.Stadium_ID WHERE c.Year IN ('2014', '2015') GROUP BY s.Stadium_ID HAVING COUNT(DISTINCT c.Year) = 2
SELECT COUNT(*) FROM concert WHERE Stadium_ID = (SELECT Stadium_ID FROM stadium ORDER BY Capacity DESC LIMIT 1)
SELECT COUNT(*) FROM concert WHERE Stadium_ID = (SELECT Stadium_ID FROM stadium ORDER BY Capacity DESC LIMIT 1)
SELECT COUNT(*) FROM Pets WHERE weight > 10
SELECT COUNT(*) FROM Pets WHERE weight > 10
SELECT weight FROM Pets WHERE PetType = 'dog' ORDER BY pet_age ASC LIMIT 1
SELECT weight FROM Pets WHERE PetType = 'dog' ORDER BY pet_age ASC LIMIT 1
SELECT PetType, MAX(weight) FROM Pets GROUP BY PetType
SELECT PetType, MAX(weight) FROM Pets GROUP BY PetType
SELECT COUNT(H.StuID) FROM Has_Pet H JOIN Student S ON H.StuID = S.StuID WHERE S.Age > 20
SELECT COUNT(*) FROM Has_Pet WHERE StuID IN (SELECT StuID FROM Student WHERE Age > 20)
SELECT COUNT(*) FROM Student JOIN Has_Pet ON Student.StuID = Has_Pet.StuID JOIN Pets ON Has_Pet.PetID = Pets.PetID WHERE Student.Sex = 'F' AND Pets.PetType = 'dog'
SELECT COUNT(*) FROM Student JOIN Has_Pet ON Student.StuID = Has_Pet.StuID JOIN Pets ON Has_Pet.PetID = Pets.PetID WHERE Student.Sex = 'F' AND Pets.PetType = 'dog'
SELECT COUNT(DISTINCT PetType) FROM Pets
SELECT COUNT(DISTINCT PetType) FROM Pets
SELECT S.Fname FROM Student S JOIN Has_Pet HP ON S.StuID = HP.StuID JOIN Pets P ON HP.PetID = P.PetID WHERE P.PetType = 'cat' OR P.PetType = 'dog'
SELECT DISTINCT S.Fname FROM Student S JOIN Has_Pet HP ON S.StuID = HP.StuID JOIN Pets P ON HP.PetID = P.PetID WHERE P.PetType = 'cat' OR P.PetType = 'dog'
SELECT S.Fname FROM Student S JOIN Has_Pet HP ON S.StuID = HP.StuID JOIN Pets P ON HP.PetID = P.PetID WHERE P.PetType = 'cat' INTERSECT SELECT S.Fname FROM Student S JOIN Has_Pet HP ON S.StuID = HP.StuID JOIN Pets P ON HP.PetID = P.PetID WHERE P.PetType = 'dog'
SELECT S.Fname FROM Student S JOIN Has_Pet HP ON S.StuID = HP.StuID JOIN Pets P ON HP.PetID = P.PetID WHERE P.PetType = 'cat' INTERSECT SELECT S.Fname FROM Student S JOIN Has_Pet HP ON S.StuID = HP.StuID JOIN Pets P ON HP.PetID = P.PetID WHERE P.PetType = 'dog'
SELECT Major, Age FROM Student WHERE StuID NOT IN (SELECT StuID FROM Has_Pet WHERE PetID IN (SELECT PetID FROM Pets WHERE PetType = 'cat'))
SELECT S.Major, S.Age FROM Student S WHERE NOT EXISTS (SELECT 1 FROM Has_Pet H JOIN Pets P ON H.PetID = P.PetID WHERE H.StuID = S.StuID AND P.PetType = 'cat')
SELECT StuID FROM Student WHERE StuID NOT IN (SELECT StuID FROM Has_Pet WHERE PetID IN (SELECT PetID FROM Pets WHERE PetType = 'cat'))
SELECT StuID FROM Student WHERE StuID NOT IN (SELECT StuID FROM Has_Pet WHERE PetID IN (SELECT PetID FROM Pets WHERE PetType = 'cat'))
SELECT S.Fname, S.Age FROM Student S JOIN Has_Pet HP ON S.StuID = HP.StuID JOIN Pets P ON HP.PetID = P.PetID WHERE P.PetType = 'dog' EXCEPT SELECT S.Fname, S.Age FROM Student S JOIN Has_Pet HP ON S.StuID = HP.StuID JOIN Pets P ON HP.PetID = P.PetID WHERE P.PetType = 'cat'
SELECT S.Fname FROM Student S JOIN Has_Pet HP ON S.StuID = HP.StuID JOIN Pets P ON HP.PetID = P.PetID WHERE P.PetType = 'dog' EXCEPT SELECT S.Fname FROM Student S JOIN Has_Pet HP ON S.StuID = HP.StuID JOIN Pets P ON HP.PetID = P.PetID WHERE P.PetType = 'cat'
SELECT PetType, weight FROM Pets WHERE pet_age = (SELECT MIN(pet_age) FROM Pets)
SELECT PetType, weight FROM Pets WHERE PetID = (SELECT PetID FROM Has_Pet WHERE StuID = (SELECT StuID FROM (SELECT StuID FROM Student ORDER BY Age ASC LIMIT 1)) ORDER BY pet_age ASC LIMIT 1)
SELECT PetID, weight FROM Pets WHERE pet_age > 1
SELECT PetID, weight FROM Pets WHERE pet_age > 1
SELECT PetType, AVG(pet_age) AS avg_age, MAX(pet_age) AS max_age FROM Pets GROUP BY PetType
SELECT PetType, AVG(pet_age) AS average_age, MAX(pet_age) AS maximum_age FROM Pets GROUP BY PetType
SELECT PetType, AVG(weight) FROM Pets JOIN Has_Pet ON Pets.PetID = Has_Pet.PetID GROUP BY PetType
SELECT PetType, AVG(weight) FROM Pets JOIN Has_Pet ON Pets.PetID = Has_Pet.PetID GROUP BY PetType
SELECT S.Fname, S.Age FROM Student S JOIN Has_Pet HP ON S.StuID = HP.StuID JOIN Pets P ON HP.PetID = P.PetID
SELECT T1.Fname, T1.Age FROM Student AS T1 JOIN Has_Pet AS T2 ON T1.StuID = T2.StuID JOIN Pets AS T3 ON T2.PetID = T3.PetID
SELECT Has_Pet.PetID FROM Has_Pet JOIN Student ON Has_Pet.StuID = Student.StuID WHERE Student.LName = 'Smith'
SELECT Has_Pet.PetID FROM Student, Has_Pet, Pets WHERE Student.LName = 'Smith' AND Student.StuID = Has_Pet.StuID AND Has_Pet.PetID = Pets.PetID
SELECT StuID, COUNT(PetID) AS Num_Pets FROM Has_Pet GROUP BY StuID
SELECT StuID, COUNT(PetID) FROM Has_Pet GROUP BY StuID
SELECT S.Fname, S.Sex FROM Student S JOIN Has_Pet HP ON S.StuID = HP.StuID GROUP BY S.StuID HAVING COUNT(HP.PetID) > 1
SELECT Fname, Sex FROM Student WHERE StuID IN (SELECT StuID FROM Has_Pet GROUP BY StuID HAVING COUNT(PetID) > 1)
SELECT S.LName FROM Student S JOIN Has_Pet HP ON S.StuID = HP.StuID JOIN Pets P ON HP.PetID = P.PetID WHERE P.PetType = 'cat' AND P.pet_age = 3
SELECT S.LName FROM Student S JOIN Has_Pet HP ON S.StuID = HP.StuID JOIN Pets P ON HP.PetID = P.PetID WHERE P.PetType = 'cat' AND P.pet_age = 3
SELECT AVG(t1.Age) FROM Student AS t1 LEFT JOIN Has_Pet AS t2 ON t1.StuID = t2.StuID WHERE t2.StuID IS NULL
SELECT AVG(t1.Age) FROM Student AS t1 LEFT JOIN Has_Pet AS t2 ON t1.StuID = t2.StuID WHERE t2.StuID IS NULL
SELECT COUNT(*) FROM continents
SELECT COUNT(*) FROM continents
SELECT c.ContId, c.Continent, COUNT(co.CountryId) AS NumberOfCountries FROM continents c LEFT JOIN countries co ON c.ContId = co.Continent GROUP BY c.ContId, c.Continent
SELECT c.ContId, c.Continent, COUNT(*) AS CountryCount FROM continents c JOIN countries co ON c.ContId = co.Continent GROUP BY c.ContId, c.Continent
SELECT COUNT(*) FROM countries
SELECT COUNT(*) FROM countries
SELECT cm.FullName, cm.Id, COUNT(DISTINCT ml.Model) AS NumberOfModels FROM car_makers cm JOIN model_list ml ON cm.Id = ml.Maker GROUP BY cm.Id, cm.FullName
SELECT T1.Id, T1.FullName, COUNT(T3.Model) AS ModelCount FROM car_makers AS T1 LEFT JOIN model_list AS T3 ON T1.Id = T3.Maker GROUP BY T1.Id, T1.FullName
SELECT car_names.Model FROM car_names JOIN cars_data ON car_names.MakeId = cars_data.Id WHERE cars_data.Horsepower = (SELECT MIN(Horsepower) FROM cars_data)
SELECT T2.Model FROM car_names AS T1 JOIN model_list AS T2 ON T1.MakeId = T2.Id WHERE T1.Horsepower = (SELECT MIN(Horsepower) FROM car_names)
SELECT car_names.Model FROM cars_data JOIN car_names ON cars_data.Id = car_names.MakeId WHERE cars_data.Weight < (SELECT AVG(Weight) FROM cars_data)
SELECT car_names.Model FROM cars_data JOIN car_names ON cars_data.Id = car_names.MakeId WHERE cars_data.Weight < (SELECT AVG(Weight) FROM cars_data)
SELECT DISTINCT cm.Maker FROM car_names cn JOIN model_list ml ON cn.Model = ml.Model JOIN car_makers cm ON ml.Maker = cm.Id JOIN cars_data cd ON cn.MakeId = cd.Id WHERE cd.Year = 1970
SELECT DISTINCT cm.Maker FROM car_names cn JOIN model_list ml ON cn.Model = ml.Model JOIN car_makers cm ON ml.Maker = cm.Id JOIN cars_data cd ON cn.MakeId = cd.Id WHERE cd.Year = 1970
SELECT car_names.Make, cars_data.Year FROM car_names JOIN cars_data ON car_names.MakeId = cars_data.Id ORDER BY cars_data.Year ASC LIMIT 1
SELECT car_makers.Maker, cars_data.Year FROM cars_data JOIN car_names ON cars_data.Id = car_names.MakeId JOIN model_list ON car_names.Model = model_list.Model JOIN car_makers ON model_list.Maker = car_makers.Id WHERE cars_data.Year = (SELECT MIN(Year) FROM cars_data)
SELECT DISTINCT T2.Model FROM car_names AS T1 JOIN model_list AS T2 ON T1.MakeId = T2.Model JOIN cars_data AS T3 ON T1.MakeId = T3.Id WHERE T3.Year > 1980
SELECT DISTINCT T2.Model FROM cars_data AS T1 JOIN car_names AS T2 ON T1.Id = T2.MakeId WHERE T1.Year > 1980
SELECT c.Continent, COUNT(cm.Id) AS MakerCount FROM car_makers cm JOIN countries co ON cm.Country = co.CountryName JOIN continents c ON co.Continent = c.ContId GROUP BY c.Continent
SELECT c.Continent, COUNT(cm.Id) AS CarMakersCount FROM continents c LEFT JOIN countries co ON c.ContId = co.Continent LEFT JOIN car_makers cm ON co.CountryId = cm.Country GROUP BY c.Continent
SELECT CountryName FROM countries WHERE CountryId IN (SELECT Country FROM car_makers GROUP BY CountryId ORDER BY COUNT(*) DESC LIMIT 1)
SELECT CountryName FROM countries WHERE CountryId = (SELECT Country FROM car_makers GROUP BY CountryId ORDER BY COUNT(*) DESC LIMIT 1)
SELECT cm.FullName, COUNT(DISTINCT ml.Model) AS ModelCount FROM car_makers cm JOIN model_list ml ON cm.Id = ml.Maker GROUP BY cm.FullName
SELECT cm.Id, cm.FullName, COUNT(DISTINCT ml.Model) AS NumModels FROM car_makers cm JOIN model_list ml ON cm.Id = ml.Maker GROUP BY cm.Id, cm.FullName
SELECT t5.Accelerate FROM car_makers AS cm JOIN countries AS c ON cm.Country = c.CountryName JOIN model_list AS ml ON cm.Id = ml.Maker JOIN car_names AS cn ON ml.Model = cn.Model JOIN cars_data AS cd ON cn.MakeId = cd.Id WHERE cm.Maker = 'amc' AND cn.Model = 'hornet sportabout (sw)'
SELECT cars_data.Accelerate FROM cars_data JOIN car_names ON cars_data.Id = car_names.MakeId JOIN model_list ON car_names.Model = model_list.Model JOIN car_makers ON model_list.Maker = car_makers.Id JOIN countries ON car_makers.Country = countries.CountryId JOIN continents ON countries.Continent = continents.ContId WHERE car_names.Model = 'amc hornet sportabout (sw)'
SELECT COUNT(*) FROM car_makers WHERE Country = 'France'
SELECT COUNT(DISTINCT car_makers.Id) FROM car_makers JOIN countries ON car_makers.Country = countries.CountryName WHERE countries.CountryName = 'France'
SELECT COUNT(DISTINCT car_names.Model) FROM car_names JOIN model_list ON car_names.Model = model_list.Model JOIN car_makers ON model_list.Maker = car_makers.Id JOIN countries ON car_makers.Country = countries.CountryId JOIN continents ON countries.Continent = continents.ContId WHERE continents.Continent = 'North America' AND countries.Country = 'USA'
SELECT COUNT(DISTINCT car_names.Model) FROM car_names JOIN model_list ON car_names.Model = model_list.Model JOIN car_makers ON model_list.Maker = car_makers.Id JOIN countries ON car_makers.Country = countries.CountryId WHERE countries.CountryName = 'United States'
SELECT AVG(T2.MPG) FROM cars_data AS T2 JOIN car_names AS T1 ON T2.Id = T1.MakeId WHERE T1.Make IN (SELECT Model FROM model_list WHERE Maker IN (SELECT Id FROM car_makers WHERE Cylinders = 4))
SELECT AVG(MPG) FROM cars_data WHERE Cylinders = 4
SELECT MIN(cars_data.Weight) FROM cars_data JOIN car_names ON cars_data.Id = car_names.MakeId JOIN model_list ON car_names.Model = model_list.Model JOIN car_makers ON model_list.Maker = car_makers.Id JOIN countries ON car_makers.Country = countries.CountryId JOIN continents ON countries.Continent = continents.ContId WHERE model_list.Cylinders = 8 AND cars_data.Year = 1974
SELECT MIN(cd.Weight) FROM cars_data cd JOIN car_names cn ON cd.Id = cn.MakeId JOIN model_list ml ON cn.Model = ml.Model JOIN car_makers cm ON ml.Maker = cm.Id JOIN countries c ON cm.Country = c.CountryName WHERE ml.Cylinders = 8 AND cd.Year = 1974
SELECT car_makers.Maker, model_list.Model FROM car_makers JOIN model_list ON car_makers.Id = model_list.Maker
SELECT car_makers.Maker, car_names.Model FROM car_makers JOIN model_list ON car_makers.Id = model_list.Maker JOIN car_names ON model_list.Model = car_names.Model
SELECT CountryId, CountryName FROM countries WHERE CountryName IN (SELECT Country FROM car_makers)
SELECT CountryId, CountryName FROM countries WHERE CountryId IN (SELECT Country FROM car_makers)
SELECT COUNT(*) FROM cars_data WHERE Horsepower > 150
SELECT COUNT(*) FROM car_names AS T1 JOIN model_list AS T2 ON T1.MakeId = T2.Id JOIN car_makers AS T3 ON T2.Maker = T3.Id WHERE T3.Horsepower > '150'
SELECT Year, AVG(Weight) AS AverageWeight FROM cars_data GROUP BY Year
SELECT Year, AVG(Weight) FROM cars_data GROUP BY Year
SELECT c.CountryName FROM countries c JOIN car_makers cm ON c.CountryId = cm.Country JOIN continents ct ON c.Continent = ct.ContId WHERE ct.Continent = 'Europe' GROUP BY c.CountryName HAVING COUNT(cm.Id) >= 3
SELECT c.CountryName FROM countries c JOIN car_makers cm ON c.CountryId = cm.Country GROUP BY c.CountryName HAVING COUNT(cm.Id) >= 3 AND c.Continent = 'Europe'
SELECT MAX(cars_data.Horsepower) AS MaxHorsepower, car_names.Make FROM cars_data JOIN car_names ON cars_data.Id = car_names.MakeId WHERE cars_data.Cylinders = 3 GROUP BY car_names.Make
SELECT car_names.Make, MAX(cars_data.MPG) AS LargestHorsepower FROM cars_data JOIN car_names ON cars_data.Id = car_names.MakeId JOIN model_list ON car_names.Model = model_list.Model WHERE model_list.Cylinders = 3 GROUP BY car_names.Make
SELECT car_names.Model FROM car_names JOIN cars_data ON car_names.MakeId = cars_data.Id ORDER BY cars_data.MPG DESC LIMIT 1
SELECT T2.Model FROM car_names AS T1 JOIN model_list AS T2 ON T1.MakeId = T2.Id JOIN cars_data AS T3 ON T3.Id = T1.MakeId WHERE T3.MPG = (SELECT MAX(MPG) FROM cars_data)
SELECT AVG(CAST(REPLACE(SUBSTR(CARS_DATA.Horsepower, 1, LENGTH(CARS_DATA.Horsepower) - 1), ',', '') AS REAL)) AS AverageHorsepower FROM CARS_DATA WHERE Year < 1980
SELECT AVG(CAST(REPLACE(SUBSTR(CARS_DATA.Horsepower, 1, LENGTH(CARS_DATA.Horsepower) - 1), ',', '') AS REAL)) AS AverageHorsepower FROM CARS_DATA WHERE Year < 1980
SELECT AVG(T4.Edispl) FROM car_names AS T1 JOIN model_list AS T2 ON T1.Model = T2.Model JOIN car_makers AS T3 ON T2.Maker = T3.Id JOIN cars_data AS T4 ON T1.MakeId = T4.Id WHERE T1.Make = 'volvo'
SELECT AVG(T4.Edispl) FROM car_names AS T1 JOIN model_list AS T2 ON T1.Model = T2.Model JOIN car_makers AS T3 ON T2.Maker = T3.Id JOIN cars_data AS T4 ON T1.MakeId = T4.Id WHERE T3.Maker = 'Volvo'
SELECT Cylinders, MAX(Accelerate) FROM cars_data GROUP BY Cylinders
SELECT MAX(cars_data.Accelerate) FROM cars_data INNER JOIN car_names ON cars_data.Id = car_names.MakeId INNER JOIN model_list ON car_names.Model = model_list.Model INNER JOIN car_makers ON model_list.Maker = car_makers.Id INNER JOIN countries ON car_makers.Country = countries.CountryId INNER JOIN continents ON countries.Continent = continents.ContId GROUP BY cars_data.Cylinders
SELECT model_list.Model FROM model_list JOIN car_names ON model_list.Model = car_names.Model GROUP BY model_list.Model ORDER BY COUNT(car_names.Model) DESC LIMIT 1
SELECT car_names.Model FROM car_names JOIN model_list ON car_names.Model = model_list.Model JOIN cars_data ON car_names.MakeId = cars_data.Id GROUP BY car_names.Model ORDER BY COUNT(DISTINCT cars_data.Id) DESC LIMIT 1
SELECT COUNT(*) FROM cars_data WHERE Cylinders > 4
SELECT COUNT(*) FROM cars_data WHERE Cylinders > 4
SELECT COUNT(*) FROM cars_data WHERE Year = 1980
SELECT COUNT(*) FROM cars_data WHERE Year = 1980
SELECT COUNT(DISTINCT ml.Model) FROM car_makers cm JOIN model_list ml ON cm.Id = ml.Maker WHERE cm.FullName = 'American Motor Company'
SELECT COUNT(DISTINCT ml.Model) FROM car_names cn JOIN model_list ml ON cn.Model = ml.Model JOIN car_makers cm ON ml.Maker = cm.Id WHERE cm.FullName = 'American Motor Company'
SELECT cm.Id, cm.FullName FROM car_makers cm JOIN model_list ml ON cm.Id = ml.Maker GROUP BY cm.Id, cm.FullName HAVING COUNT(ml.Model) > 3
SELECT Id, Maker FROM car_makers WHERE Id IN (SELECT Maker FROM model_list GROUP BY Maker HAVING COUNT(Model) > 3)
SELECT DISTINCT T2.Model FROM car_names AS T1 JOIN model_list AS T2 ON T1.MakeId = T2.Model JOIN car_makers AS T3 ON T2.Maker = T3.Id WHERE T3.FullName = 'General Motors' OR T1.Make IN (SELECT T4.Model FROM cars_data AS T4 JOIN car_names AS T5 ON T4.Id = T5.MakeId WHERE T4.Weight > 3500)
SELECT DISTINCT T2.Model FROM car_names AS T1 JOIN model_list AS T2 ON T1.MakeId = T2.Model JOIN car_makers AS T3 ON T2.Maker = T3.Id WHERE T3.FullName IN ('General Motors') UNION SELECT T4.Model FROM cars_data AS T4 JOIN car_names AS T5 ON T4.Id = T5.MakeId WHERE T4.Weight > 3500
SELECT Year FROM cars_data WHERE Weight >= 3000 AND Weight <= 4000
SELECT DISTINCT T1.Year FROM cars_data AS T1 JOIN car_names AS T2 ON T1.Id = T2.MakeId WHERE T1.Weight < 4000 INTERSECT SELECT DISTINCT T1.Year FROM cars_data AS T1 JOIN car_names AS T2 ON T1.Id = T2.MakeId WHERE T1.Weight > 3000
SELECT Horsepower FROM cars_data WHERE Accelerate = (SELECT MAX(Accelerate) FROM cars_data)
SELECT T2.Horsepower FROM cars_data AS T1 JOIN car_names AS T2 ON T1.Id = T2.MakeId ORDER BY T1.Accelerate DESC LIMIT 1
SELECT model_list.Cylinders FROM cars_data JOIN car_names ON cars_data.Id = car_names.MakeId JOIN model_list ON car_names.Model = model_list.Model JOIN car_makers ON car_names.Make = car_makers.Maker WHERE car_makers.Country = 'volvo' ORDER BY cars_data.Accelerate LIMIT 1
SELECT model_list.Cylinders FROM car_names JOIN model_list ON car_names.Model = model_list.Model JOIN car_makers ON car_names.Make = car_makers.Maker WHERE car_makers.Country = 'Volvo' ORDER BY cars_data.Accelerate LIMIT 1
SELECT COUNT(*) FROM cars_data WHERE Accelerate > (SELECT Horsepower FROM cars_data WHERE Horsepower IS NOT NULL ORDER BY Horsepower DESC LIMIT 1)
SELECT COUNT(*) FROM cars_data WHERE Accelerate > (SELECT Horsepower FROM cars_data WHERE Horsepower IS NOT NULL ORDER BY Horsepower DESC LIMIT 1)
SELECT COUNT(DISTINCT c.CountryId) FROM countries c JOIN car_makers cm ON c.CountryId = cm.Country WHERE cm.Id IS NOT NULL GROUP BY c.CountryId HAVING COUNT(cm.Id) > 2
SELECT COUNT(DISTINCT c.CountryId) FROM countries c JOIN car_makers cm ON c.CountryId = SUBSTR(cm.Country, 1, INSTR(cm.Country, '(') - 1) GROUP BY c.CountryId HAVING COUNT(cm.Id) > 2
SELECT COUNT(*) FROM cars_data WHERE Cylinders > 6
SELECT COUNT(*) FROM cars_data WHERE Cylinders > 6
SELECT T2.Model FROM model_list AS T1 JOIN car_names AS T2 ON T1.Id = T2.MakeId JOIN cars_data AS T3 ON T3.Id = T2.MakeId WHERE T1.Cylinders = 4 ORDER BY T3.Horsepower DESC LIMIT 1
SELECT T2.Model FROM cars_data AS T1 JOIN car_names AS T2 ON T1.Id = T2.MakeId JOIN model_list AS T3 ON T2.Model = T3.Model JOIN car_makers AS T4 ON T3.Maker = T4.Id WHERE T3.Cylinders = 4 ORDER BY T1.Horsepower DESC LIMIT 1
SELECT cn.MakeId, cm.Make FROM cars_data cd JOIN car_names cn ON cd.Id = cn.MakeId JOIN model_list ml ON cn.Model = ml.Model JOIN car_makers cm ON ml.Maker = cm.Id WHERE cd.Horsepower > (SELECT MIN(Horsepower) FROM cars_data) AND ml.Maker IN (SELECT Maker FROM model_list WHERE Cylinders <= 3)
SELECT DISTINCT c.Id, cn.Model FROM cars_data cd JOIN car_names cn ON cd.Id = cn.MakeId JOIN model_list ml ON cn.Model = ml.Model JOIN car_makers cm ON ml.Maker = cm.Id JOIN countries co ON cm.Country = co.CountryName JOIN continents ct ON co.Continent = ct.ContId WHERE cd.Horsepower < (SELECT MIN(Horsepower) FROM cars_data) AND cd.Cylinders < 4
SELECT MAX(cars_data.MPG) FROM cars_data WHERE Cylinders = 8 OR Year < 1980
SELECT MAX(T2.MPG) FROM model_list AS T1 JOIN cars_data AS T2 ON T1.MakeId = T2.Id WHERE T1.Cylinders = 8 OR T2.Year < 1980
SELECT DISTINCT T2.Model FROM car_names AS T1 JOIN model_list AS T2 ON T1.MakeId = T2.Id JOIN car_makers AS T3 ON T2.Maker = T3.Id JOIN cars_data AS T4 ON T1.MakeId = T4.Id WHERE T4.Weight < 3500 AND T3.FullName != 'Ford Motor Company'
SELECT DISTINCT T2.Model FROM car_names AS T1 JOIN model_list AS T2 ON T1.MakeId = T2.MakeId JOIN car_makers AS T3 ON T2.Maker = T3.Id JOIN cars_data AS T4 ON T1.MakeId = T4.Id WHERE T4.Weight < 3500 AND T3.FullName != 'Ford Motor Company'
SELECT CountryName FROM countries WHERE CountryId NOT IN (SELECT Country FROM car_makers)
SELECT CountryName FROM countries WHERE CountryId NOT IN (SELECT Country FROM car_makers)
SELECT cm.Id, cm.Maker FROM car_makers cm JOIN model_list ml ON cm.Id = ml.Maker GROUP BY cm.Id, cm.Maker HAVING COUNT(ml.Model) >= 2 AND COUNT(DISTINCT cm.Country) > 3
SELECT cm.Id, cm.Maker FROM car_makers cm JOIN model_list ml ON cm.Id = ml.Maker GROUP BY cm.Id, cm.Maker HAVING COUNT(ml.Model) >= 2 AND (SELECT COUNT(cn.MakeId) FROM car_names cn WHERE cn.Make = cm.Maker AND cn.Model IN (SELECT ml.Model FROM model_list ml WHERE ml.Maker = cm.Id)) > 3
SELECT c.CountryId, c.CountryName FROM countries c WHERE c.CountryId IN ( SELECT cm.Country FROM car_makers cm GROUP BY cm.Country HAVING COUNT(cm.Id) > 3 ) OR c.Country = (SELECT cm.Country FROM car_makers cm WHERE cm.Maker = (SELECT ml.Maker FROM model_list ml WHERE ml.Model = 'fiat'))
SELECT CountryId, CountryName FROM countries WHERE CountryId IN (SELECT Country FROM car_makers GROUP BY Country HAVING COUNT(Id) > 3) UNION SELECT CountryId, CountryName FROM countries WHERE CountryId IN (SELECT CountryId FROM car_makers WHERE Maker IN (SELECT Id FROM car_makers WHERE Country = (SELECT Country FROM car_names WHERE Model = 'Fiat'))
SELECT Country FROM airlines WHERE Airline = 'JetBlue Airways'
SELECT Country FROM airlines WHERE Airline = 'Jetblue Airways'
SELECT Abbreviation FROM airlines WHERE Airline = 'JetBlue Airways'
SELECT Abbreviation FROM airlines WHERE Airline = 'Jetblue Airways'
SELECT Airline, Abbreviation FROM airlines WHERE Country = 'USA'
SELECT Airline, Abbreviation FROM airlines WHERE Country = 'USA'
SELECT AirportCode, AirportName FROM airports WHERE City = 'Anthony'
SELECT AirportCode, AirportName FROM airports WHERE City = 'Anthony'
SELECT COUNT(*) FROM airlines
SELECT COUNT(*) FROM airlines
SELECT COUNT(*) FROM airports
SELECT COUNT(DISTINCT AirportCode) FROM airports
SELECT COUNT(*) FROM flights
SELECT COUNT(*) FROM flights
SELECT Airline FROM airlines WHERE Abbreviation = 'UAL'
SELECT Airline FROM airlines WHERE Abbreviation = 'UAL'
SELECT COUNT(*) FROM airlines WHERE Country = 'USA'
SELECT COUNT(*) FROM airlines WHERE Country = 'USA'
SELECT City, Country FROM airports WHERE AirportName = 'Alton'
SELECT City, Country FROM airports WHERE AirportName = 'Alton'
SELECT AirportName FROM airports WHERE AirportCode = 'AKO'
SELECT AirportName FROM airports WHERE AirportCode = 'AKO'
SELECT AirportName FROM airports WHERE City = 'Aberdeen'
SELECT AirportName FROM airports WHERE City = 'Aberdeen'
SELECT COUNT(*) FROM flights WHERE SourceAirport = 'APG'
SELECT COUNT(*) FROM flights WHERE SourceAirport = (SELECT AirportCode FROM airports WHERE AirportName = 'APG')
SELECT COUNT(*) FROM flights WHERE DestAirport = 'ATO'
SELECT COUNT(*) FROM flights WHERE DestAirport = (SELECT AirportCode FROM airports WHERE AirportName = 'ATO')
SELECT COUNT(*) FROM flights WHERE SourceAirport = (SELECT AirportCode FROM airports WHERE City = 'Aberdeen')
SELECT COUNT(*) FROM flights WHERE SourceAirport = (SELECT AirportCode FROM airports WHERE City = 'Aberdeen')
SELECT COUNT(*) FROM flights WHERE DestAirport = (SELECT AirportCode FROM airports WHERE City = 'Aberdeen')
SELECT COUNT(*) FROM flights WHERE DestAirport = (SELECT AirportCode FROM airports WHERE City = 'Aberdeen')
SELECT COUNT(*) FROM flights f JOIN airports a ON f.SourceAirport = a.AirportCode JOIN airports d ON f.DestAirport = d.AirportCode WHERE a.City = 'Aberdeen' AND d.City = 'Ashley'
SELECT COUNT(*) FROM flights WHERE SourceAirport = (SELECT AirportCode FROM airports WHERE City = 'Aberdeen') AND DestAirport = (SELECT AirportCode FROM airports WHERE City = 'Ashley')
SELECT COUNT(*) FROM flights WHERE Airline = (SELECT uid FROM airlines WHERE Airline = 'JetBlue Airways')
SELECT COUNT(*) FROM flights f JOIN airlines a ON f.Airline = a.uid WHERE a.Airline = 'Jetblue Airways'
SELECT COUNT(*) FROM flights f JOIN airlines a ON f.Airline = a.uid JOIN airports p ON f.DestAirport = p.AirportCode WHERE a.Airline = 'United Airlines' AND p.AirportName = 'ASY'
SELECT COUNT(*) FROM flights f JOIN airlines a ON f.Airline = a.uid JOIN airports p ON f.DestAirport = p.AirportCode WHERE a.Airline = 'United' AND p.City = 'ASY'
SELECT COUNT(*) FROM flights WHERE Airline = (SELECT uid FROM airlines WHERE Airline = 'United Airlines') AND SourceAirport = (SELECT AirportCode FROM airports WHERE AirportName = 'AHD')
SELECT COUNT(*) FROM flights f JOIN airlines a ON f.Airline = a.uid JOIN airports p ON f.SourceAirport = p.AirportCode WHERE a.Airline = 'United Airlines' AND p.City = 'AHD'
SELECT COUNT(*) FROM flights f JOIN airlines a ON f.Airline = a.uid JOIN airports p ON f.DestAirport = p.AirportCode WHERE a.Airline = 'United' AND p.City = 'Aberdeen'
SELECT COUNT(*) FROM flights f JOIN airlines a ON f.Airline = a.uid JOIN airports p ON f.DestAirport = p.AirportCode WHERE a.Airline = 'United' AND p.City = 'Aberdeen'
SELECT T2.City FROM flights AS T1 JOIN airports AS T2 ON T1.DestAirport = T2.AirportCode GROUP BY T2.City ORDER BY COUNT(T1.DestAirport) DESC LIMIT 1
SELECT T2.City FROM flights AS T1 JOIN airports AS T2 ON T1.DestAirport = T2.AirportCode GROUP BY T2.City ORDER BY COUNT(T2.City) DESC LIMIT 1
SELECT T2.City FROM flights AS T1 JOIN airports AS T2 ON T1.SourceAirport = T2.AirportCode GROUP BY T2.City ORDER BY COUNT(T1.SourceAirport) DESC LIMIT 1
SELECT T2.City FROM flights AS T1 JOIN airports AS T2 ON T1.SourceAirport = T2.AirportCode GROUP BY T2.City ORDER BY COUNT(T2.City) DESC LIMIT 1
SELECT T2.AirportCode FROM flights AS T1 JOIN airports AS T2 ON T1.SourceAirport = T2.AirportCode GROUP BY T2.AirportCode ORDER BY COUNT(T1.FlightNo) DESC LIMIT 1
SELECT T2.AirportCode FROM flights AS T1 JOIN airports AS T2 ON T1.SourceAirport = T2.AirportCode GROUP BY T2.AirportCode ORDER BY COUNT(T1.FlightNo) DESC LIMIT 1
SELECT AirportCode FROM airports WHERE AirportCode IN (SELECT SourceAirport FROM flights GROUP BY SourceAirport UNION SELECT DestAirport FROM flights GROUP BY DestAirport) GROUP BY AirportCode ORDER BY COUNT(*) ASC LIMIT 1
SELECT SourceAirport FROM flights GROUP BY SourceAirport ORDER BY COUNT(*) ASC LIMIT 1
SELECT A.Airline FROM flights F JOIN airlines A ON F.Airline = A.uid GROUP BY A.Airline ORDER BY COUNT(F.Airline) DESC LIMIT 1
SELECT Airline, COUNT(*) AS flight_count FROM flights GROUP BY Airline ORDER BY flight_count DESC LIMIT 1
SELECT a.Abbreviation, a.Country FROM airlines a JOIN flights f ON a.uid = f.Airline GROUP BY a.uid, a.Abbreviation, a.Country HAVING COUNT(f.FlightNo) = (SELECT MIN(cnt) FROM (SELECT COUNT(*) AS cnt FROM flights GROUP BY Airline) sub)
SELECT a.Abbreviation, a.Country FROM airlines a JOIN flights f ON a.uid = f.Airline GROUP BY a.uid, a.Abbreviation, a.Country HAVING COUNT(f.FlightNo) = (SELECT COUNT(f2.FlightNo) FROM flights f2 GROUP BY f2.Airline ORDER BY COUNT(f2.FlightNo) ASC LIMIT 1)
SELECT DISTINCT A.Airline FROM flights AS F JOIN airlines AS A ON F.Airline = A.uid WHERE F.SourceAirport = 'AHD'
SELECT DISTINCT T1.Airline FROM flights AS T1 JOIN airports AS T2 ON T1.SourceAirport = T2.AirportCode WHERE T2.AirportName = 'AHD'
SELECT DISTINCT A.Airline FROM flights F JOIN airlines A ON F.Airline = A.uid WHERE F.DestAirport = 'AHD'
SELECT DISTINCT T1.Airline FROM flights AS T1 JOIN airports AS T2 ON T1.DestAirport = T2.AirportCode WHERE T2.AirportCode = 'AHD'
SELECT DISTINCT a.Airline FROM flights f JOIN airlines a ON f.Airline = a.uid WHERE f.SourceAirport IN ('APG', 'CVO') GROUP BY a.Airline HAVING COUNT(DISTINCT f.SourceAirport) = 2
SELECT DISTINCT a.Airline FROM flights f JOIN airlines a ON f.Airline = a.uid WHERE f.SourceAirport IN ('APG', 'CVO') GROUP BY a.Airline HAVING COUNT(DISTINCT f.SourceAirport) = 2
SELECT DISTINCT a.Airline FROM flights f JOIN airlines a ON f.Airline = a.uid WHERE f.SourceAirport = 'CVO' AND f.DestAirport NOT IN (SELECT SourceAirport FROM flights WHERE SourceAirport = 'APG')
SELECT DISTINCT a.Airline FROM flights f JOIN airlines a ON f.Airline = a.uid WHERE f.SourceAirport = 'CVO' AND NOT EXISTS (SELECT 1 FROM flights WHERE Airline = f.Airline AND SourceAirport = 'APG')
SELECT A.Airline FROM flights F JOIN airlines A ON F.Airline = A.uid GROUP BY A.Airline HAVING COUNT(F.FlightNo) >= 10
SELECT Airline FROM flights GROUP BY Airline HAVING COUNT(*) >= 10
SELECT A.Airline FROM airlines A JOIN flights F ON A.uid = F.Airline GROUP BY A.Airline HAVING COUNT(F.FlightNo) < 200
SELECT Airline FROM flights GROUP BY Airline HAVING COUNT(*) < 200
SELECT FlightNo FROM flights WHERE Airline = (SELECT uid FROM airlines WHERE Airline = 'United Airlines')
SELECT FlightNo FROM flights WHERE Airline = (SELECT uid FROM airlines WHERE Airline = 'United Airlines')
SELECT FlightNo FROM flights WHERE SourceAirport = (SELECT AirportCode FROM airports WHERE AirportName = 'APG')
SELECT FlightNo FROM flights WHERE SourceAirport = (SELECT AirportCode FROM airports WHERE AirportName = 'APG')
SELECT FlightNo FROM flights WHERE DestAirport = (SELECT AirportCode FROM airports WHERE AirportName = "APG")
SELECT FlightNo FROM flights WHERE DestAirport = (SELECT AirportCode FROM airports WHERE AirportName = 'APG')
SELECT FlightNo FROM flights WHERE SourceAirport = (SELECT AirportCode FROM airports WHERE City = 'Aberdeen')
SELECT FlightNo FROM flights WHERE SourceAirport = (SELECT AirportCode FROM airports WHERE City = 'Aberdeen')
SELECT FlightNo FROM flights WHERE DestAirport = (SELECT AirportCode FROM airports WHERE City = 'Aberdeen')
SELECT FlightNo FROM flights WHERE DestAirport = (SELECT AirportCode FROM airports WHERE City = 'Aberdeen')
SELECT COUNT(*) FROM flights WHERE DestAirport IN (SELECT AirportCode FROM airports WHERE City IN ('Aberdeen', 'Abilene'))
SELECT COUNT(*) FROM flights WHERE DestAirport IN (SELECT AirportCode FROM airports WHERE City IN ('Aberdeen', 'Abilene'))
SELECT AirportName FROM airports WHERE AirportCode NOT IN (SELECT SourceAirport FROM flights UNION SELECT DestAirport FROM flights)
SELECT AirportName FROM airports WHERE AirportCode NOT IN (SELECT SourceAirport FROM flights UNION SELECT DestAirport FROM flights)
SELECT COUNT(*) FROM employee
SELECT COUNT(*) FROM employee
SELECT Name FROM employee ORDER BY Age ASC
SELECT Name FROM employee ORDER BY Age ASC
SELECT City, COUNT(*) FROM employee GROUP BY City
SELECT City, COUNT(*) FROM employee GROUP BY City
SELECT City FROM employee WHERE Age < 30 GROUP BY City HAVING COUNT(*) > 1
SELECT City FROM employee WHERE Age < 30 GROUP BY City HAVING COUNT(*) > 1
SELECT Location, COUNT(*) FROM shop GROUP BY Location
SELECT Location, COUNT(*) FROM shop GROUP BY Location
SELECT Manager_name, District FROM shop WHERE Number_products = (SELECT MAX(Number_products) FROM shop)
SELECT Manager_name, District FROM shop WHERE Number_products = (SELECT MAX(Number_products) FROM shop)
SELECT MIN(Number_products), MAX(Number_products) FROM shop
SELECT MIN(Number_products), MAX(Number_products) FROM shop
SELECT Name, Location, District FROM shop ORDER BY Number_products DESC
SELECT Name, Location, District FROM shop ORDER BY Number_products DESC
SELECT Name FROM shop WHERE Number_products > (SELECT AVG(Number_products) FROM shop)
SELECT s.Name FROM shop s JOIN hiring h ON s.Shop_ID = h.Shop_ID GROUP BY s.Shop_ID, s.Name HAVING AVG(s.Number_products) > AVG(s.Number_products)
SELECT e.Name FROM employee e JOIN evaluation ev ON e.Employee_ID = ev.Employee_ID GROUP BY e.Employee_ID ORDER BY COUNT(ev.Year_awarded) DESC LIMIT 1
SELECT e.Name FROM employee e JOIN evaluation ev ON e.Employee_ID = ev.Employee_ID GROUP BY e.Employee_ID ORDER BY COUNT(ev.Employee_ID) DESC LIMIT 1
SELECT e.Name FROM employee e JOIN evaluation ev ON e.Employee_ID = ev.Employee_ID ORDER BY ev.Bonus DESC LIMIT 1
SELECT employee.Name FROM employee JOIN evaluation ON employee.Employee_ID = evaluation.Employee_ID ORDER BY evaluation.Bonus DESC LIMIT 1
SELECT Name FROM employee WHERE Employee_ID NOT IN (SELECT Employee_ID FROM evaluation)
SELECT Name FROM employee WHERE Employee_ID NOT IN (SELECT Employee_ID FROM evaluation)
SELECT T2.Name FROM hiring AS T1 JOIN shop AS T2 ON T1.Shop_ID = T2.Shop_ID GROUP BY T1.Shop_ID ORDER BY COUNT(T1.Employee_ID) DESC LIMIT 1
SELECT S.Name FROM shop S JOIN hiring H ON S.Shop_ID = H.Shop_ID GROUP BY S.Name ORDER BY COUNT(H.Employee_ID) DESC LIMIT 1
SELECT Name FROM shop WHERE Shop_ID NOT IN (SELECT Shop_ID FROM hiring)
SELECT s.Name FROM shop s LEFT JOIN hiring h ON s.Shop_ID = h.Shop_ID WHERE h.Employee_ID IS NULL
SELECT s.Name AS Shop_Name, COUNT(h.Employee_ID) AS Number_of_Employees_Hired FROM shop s JOIN hiring h ON s.Shop_ID = h.Shop_ID GROUP BY s.Shop_ID, s.Name
SELECT s.Name, COUNT(h.Employee_ID) AS Number_of_Employees FROM shop s LEFT JOIN hiring h ON s.Shop_ID = h.Shop_ID GROUP BY s.Shop_ID, s.Name
SELECT SUM(Bonus) FROM evaluation
SELECT SUM(Bonus) FROM evaluation
SELECT * FROM hiring
SELECT * FROM hiring
SELECT DISTINCT T2.District FROM shop AS T1 JOIN shop AS T2 ON T1.District = T2.District WHERE T1.Number_products < 3000 AND T2.Number_products > 10000
SELECT DISTINCT T2.District FROM shop AS T1 JOIN employee_hire_evaluation.shop AS T2 ON T1.District = T2.District WHERE T1.Number_products < 3000 INTERSECT SELECT DISTINCT T2.District FROM shop AS T1 JOIN employee_hire_evaluation.shop AS T2 ON T1.District = T2.District WHERE T1.Number_products > 10000
SELECT COUNT(DISTINCT Location) FROM shop
SELECT COUNT(DISTINCT Location) FROM shop
SELECT COUNT(DISTINCT Document_ID) FROM Documents
SELECT COUNT(*) FROM Documents
SELECT Document_ID, Document_Name, Document_Description FROM Documents
SELECT Document_ID, Document_Name, Document_Description FROM Documents
SELECT Document_Name, Template_ID FROM Documents WHERE Document_Description LIKE '%w%'
SELECT Document_Name, Template_ID FROM Documents WHERE Document_Description LIKE '%w%'
SELECT Documents.Document_ID, Documents.Template_ID, Documents.Document_Description FROM Documents WHERE Documents.Document_Name = 'Robbin CV'
SELECT Documents.Document_ID, Documents.Template_ID, Documents.Document_Description FROM Documents WHERE Documents.Document_Name = 'Robbin CV'
SELECT COUNT(DISTINCT Template_ID) FROM Documents
SELECT COUNT(DISTINCT Template_ID) FROM Documents
SELECT COUNT(DISTINCT Documents.Document_ID) FROM Documents JOIN Templates ON Documents.Template_ID = Templates.Template_ID JOIN Ref_Template_Types ON Templates.Template_Type_Code = Ref_Template_Types.Template_Type_Code WHERE Ref_Template_Types.Template_Type_Code = 'PPT'
SELECT COUNT(DISTINCT d.Document_ID) FROM Documents d JOIN Templates t ON d.Template_ID = t.Template_ID JOIN Ref_Template_Types r ON t.Template_Type_Code = r.Template_Type_Code WHERE r.Template_Type_Code = 'PPT'
SELECT Templates.Template_ID, COUNT(Documents.Document_ID) AS Number_of_Documents FROM Templates LEFT JOIN Documents ON Templates.Template_ID = Documents.Template_ID GROUP BY Templates.Template_ID
SELECT Template_ID, COUNT(*) FROM Documents GROUP BY Template_ID
SELECT T.Template_ID, RT.Template_Type_Code FROM Templates T JOIN Documents D ON T.Template_ID = D.Template_ID JOIN Ref_Template_Types RT ON T.Template_Type_Code = RT.Template_Type_Code GROUP BY T.Template_ID, RT.Template_Type_Code ORDER BY COUNT(D.Document_ID) DESC LIMIT 1
SELECT T.Template_ID, T.Template_Type_Code FROM Templates T JOIN Documents D ON T.Template_ID = D.Template_ID GROUP BY T.Template_ID, T.Template_Type_Code ORDER BY COUNT(D.Document_ID) DESC LIMIT 1
SELECT Template_ID FROM Documents GROUP BY Template_ID HAVING COUNT(DOCUMENT_ID) > 1
SELECT Template_ID FROM Documents GROUP BY Template_ID HAVING COUNT(DISTINCT Document_ID) > 1
SELECT Template_ID FROM Templates WHERE Template_ID NOT IN (SELECT Template_ID FROM Documents)
SELECT Template_ID FROM Templates WHERE Template_ID NOT IN (SELECT Template_ID FROM Documents)
SELECT COUNT(DISTINCT Template_ID) FROM Templates
SELECT COUNT(*) FROM Templates
SELECT Template_ID, Version_Number, Template_Type_Code FROM Templates
SELECT Template_ID, Version_Number, Template_Type_Code FROM Templates
SELECT DISTINCT Template_Type_Code FROM Templates
SELECT DISTINCT Template_Type_Code FROM Templates JOIN Ref_Template_Types ON Templates.Template_Type_Code = Ref_Template_Types.Template_Type_Code
SELECT Template_ID FROM Templates WHERE Template_Type_Code IN ('PP', 'PPT')
SELECT Template_ID FROM Templates WHERE Template_Type_Code IN ('PP', 'PPT')
SELECT COUNT(*) FROM Templates WHERE Template_Type_Code = 'CV'
SELECT COUNT(*) FROM Templates WHERE Template_Type_Code = 'CV'
SELECT Template_Type_Code, Version_Number FROM Templates WHERE Version_Number > 5
SELECT Version_Number, Template_Type_Code FROM Templates WHERE Version_Number > 5
SELECT Template_Type_Code, COUNT(Template_ID) FROM Templates GROUP BY Template_Type_Code
SELECT Template_Type_Code, COUNT(Template_ID) FROM Templates GROUP BY Template_Type_Code
SELECT Template_Type_Code FROM Templates GROUP BY Template_Type_Code ORDER BY COUNT(Template_Type_Code) DESC LIMIT 1
SELECT Template_Type_Code FROM Templates GROUP BY Template_Type_Code ORDER BY COUNT(*) DESC LIMIT 1
SELECT Template_Type_Code FROM Templates GROUP BY Template_Type_Code HAVING COUNT(Template_ID) < 3
SELECT Template_Type_Code FROM Templates GROUP BY Template_Type_Code HAVING COUNT(Template_ID) < 3
SELECT MIN-Version_Number, Template_Type_Code FROM Templates JOIN Ref_Template_Types ON Templates.Template_Type_Code = Ref_Template_Types.Template_Type_Code GROUP BY Template_Type_Code
SELECT MIN(T.Version_Number) AS Lowest_Version, T.Template_Type_Code FROM Templates T JOIN Ref_Template_Types R ON T.Template_Type_Code = R.Template_Type_Code GROUP BY T.Template_Type_Code
SELECT T.Template_Type_Code FROM Templates T JOIN Documents D ON T.Template_ID = D.Template_ID WHERE D.Document_Name = 'Data base'
SELECT DISTINCT t.Template_Type_Code FROM Templates t JOIN Documents d ON t.Template_ID = d.Template_ID WHERE d.Document_Name = 'Data base'
SELECT Document_Name FROM Documents WHERE Template_ID IN (SELECT Template_ID FROM Templates WHERE Template_Type_Code = 'BK')
SELECT DISTINCT d.Document_Name FROM Documents d JOIN Templates t ON d.Template_ID = t.Template_ID WHERE t.Template_Type_Code = 'BK'
SELECT r.Template_Type_Code, COUNT(d.Template_ID) AS Number_of_Documents FROM Ref_Template_Types r LEFT JOIN Templates t ON r.Template_Type_Code = t.Template_Type_Code LEFT JOIN Documents d ON t.Template_ID = d.Template_ID GROUP BY r.Template_Type_Code
SELECT T2.Template_Type_Code, COUNT(T1.Template_ID) FROM Documents AS T1 JOIN Templates AS T2 ON T1.Template_ID = T2.Template_ID GROUP BY T2.Template_Type_Code
SELECT TT.Template_Type_Code FROM Templates T JOIN Documents D ON T.Template_ID = D.Template_ID JOIN Ref_Template_Types TT ON T.Template_Type_Code = TT.Template_Type_Code GROUP BY TT.Template_Type_Code ORDER BY COUNT(D.Document_ID) DESC LIMIT 1
SELECT Template_Type_Code FROM Templates INNER JOIN Documents ON Templates.Template_ID = Documents.Template_ID GROUP BY Template_Type_Code ORDER BY COUNT(*) DESC LIMIT 1
SELECT Template_Type_Code FROM Ref_Template_Types WHERE Template_Type_Code NOT IN (SELECT Template_Type_Code FROM Templates)
SELECT Template_Type_Code FROM Ref_Template_Types WHERE Template_Type_Code NOT IN (SELECT Template_Type_Code FROM Templates)
SELECT Template_Type_Code, Template_Type_Description FROM Ref_Template_Types
SELECT Template_Type_Code, Template_Type_Description FROM Ref_Template_Types
SELECT Template_Type_Description FROM Ref_Template_Types WHERE Template_Type_Code = "AD"
SELECT Template_Type_Description FROM Ref_Template_Types WHERE Template_Type_Code = 'AD'
SELECT Template_Type_Code FROM Ref_Template_Types WHERE Template_Type_Description = "Book"
SELECT Template_Type_Code FROM Ref_Template_Types WHERE Template_Type_Description = 'Book'
SELECT DISTINCT T2.Template_Type_Description FROM Templates AS T1 JOIN Ref_Template_Types AS T2 ON T1.Template_Type_Code = T2.Template_Type_Code WHERE T1.Template_ID IN (SELECT Template_ID FROM Documents)
SELECT DISTINCT RT.Template_Type_Description FROM Ref_Template_Types RT JOIN Templates T ON RT.Template_Type_Code = T.Template_Type_Code JOIN Documents D ON T.Template_ID = D.Template_ID
SELECT T.Template_ID FROM Templates T JOIN Ref_Template_Types R ON T.Template_Type_Code = R.Template_Type_Code WHERE R.Template_Type_Description = 'Presentation'
SELECT Template_ID FROM Templates WHERE Template_Type_Code = (SELECT Template_Type_Code FROM Ref_Template_Types WHERE Template_Type_Description = 'Presentation')
SELECT COUNT(Paragraph_ID) FROM Paragraphs
SELECT COUNT(Paragraph_ID) FROM Paragraphs
SELECT COUNT(*) FROM Paragraphs JOIN Documents ON Paragraphs.Document_ID = Documents.Document_ID WHERE Documents.Document_Name = 'Summer Show'
SELECT COUNT(*) FROM Paragraphs JOIN Documents ON Paragraphs.Document_ID = Documents.Document_ID WHERE Documents.Document_Name = 'Summer Show'
SELECT p.Paragraph_ID, p.Paragraph_Text, p.Other_Details FROM Paragraphs p WHERE p.Paragraph_Text = 'Korea '
SELECT p.Paragraph_Text, d.Document_Name, t.Template_Type_Description FROM Paragraphs p JOIN Documents d ON p.Document_ID = d.Document_ID JOIN Templates t ON d.Template_ID = t.Template_ID JOIN Ref_Template_Types rt ON t.Template_Type_Code = rt.Template_Type_Code WHERE p.Paragraph_Text LIKE '%Korea %'
SELECT Paragraphs.Paragraph_ID, Paragraphs.Paragraph_Text FROM Paragraphs JOIN Documents ON Paragraphs.Document_ID = Documents.Document_ID WHERE Documents.Document_Name = 'Welcome to NY'
SELECT Paragraphs.Paragraph_ID, Paragraphs.Paragraph_Text FROM Paragraphs JOIN Documents ON Paragraphs.Document_ID = Documents.Document_ID WHERE Documents.Document_Name = 'Welcome to NY'
SELECT Paragraph_Text FROM Paragraphs JOIN Documents ON Paragraphs.Document_ID = Documents.Document_ID WHERE Documents.Document_Name = 'Customer reviews'
SELECT P.Paragraph_Text FROM Paragraphs P JOIN Documents D ON P.Document_ID = D.Document_ID WHERE D.Document_Name = 'Customer reviews'
SELECT Document_ID, COUNT(Paragraph_ID) AS Number_of_Paragraphs FROM Paragraphs GROUP BY Document_ID ORDER BY Document_ID
SELECT Document_ID, COUNT(Paragraph_ID) AS Num_Paragraphs FROM Paragraphs GROUP BY Document_ID ORDER BY Document_ID
SELECT d.Document_ID, d.Document_Name, COUNT(p.Paragraph_ID) AS Number_of_Paragraphs FROM Documents d JOIN Paragraphs p ON d.Document_ID = p.Document_ID GROUP BY d.Document_ID, d.Document_Name
SELECT Documents.Document_ID, Documents.Document_Name, COUNT(Paragraphs.Paragraph_ID) AS Number_of_Paragraphs FROM Documents LEFT JOIN Paragraphs ON Documents.Document_ID = Paragraphs.Document_ID GROUP BY Documents.Document_ID, Documents.Document_Name
SELECT Document_ID FROM Paragraphs GROUP BY Document_ID HAVING COUNT(Paragraph_ID) >= 2
SELECT DISTINCT Document_ID FROM Paragraphs GROUP BY Document_ID HAVING COUNT(Paragraph_ID) >= 2
SELECT d.Document_ID, d.Document_Name FROM Documents d JOIN (SELECT Document_ID, COUNT(*) as para_count FROM Paragraphs GROUP BY Document_ID) p ON d.Document_ID = p.Document_ID ORDER BY p.para_count DESC LIMIT 1
SELECT Document_ID, Document_Name FROM Documents WHERE Document_ID = (SELECT Document_ID FROM Paragraphs GROUP BY Document_ID ORDER BY COUNT(Paragraph_ID) DESC LIMIT 1)
SELECT Document_ID FROM Paragraphs GROUP BY Document_ID ORDER BY COUNT(Paragraph_ID) ASC LIMIT 1
SELECT Document_ID FROM Paragraphs GROUP BY Document_ID ORDER BY COUNT(Paragraph_ID) ASC LIMIT 1
SELECT Document_ID FROM Paragraphs GROUP BY Document_ID HAVING COUNT(Paragraph_ID) BETWEEN 1 AND 2
SELECT DISTINCT Document_ID FROM Paragraphs WHERE Paragraph_ID BETWEEN 1 AND 2
SELECT DISTINCT p.Document_ID FROM Paragraphs p WHERE p.Paragraph_Text = 'Brazil' INTERSECT SELECT DISTINCT p.Document_ID FROM Paragraphs p WHERE p.Paragraph_Text = 'Ireland'
SELECT DISTINCT d.Document_ID FROM Documents d JOIN Paragraphs p ON d.Document_ID = p.Document_ID WHERE p.Paragraph_Text = 'Brazil' INTERSECT SELECT DISTINCT d.Document_ID FROM Documents d JOIN Paragraphs p ON d.Document_ID = p.Document_ID WHERE p.Paragraph_Text = 'Ireland'
SELECT COUNT(DISTINCT Teacher_ID) FROM course_arrange
SELECT COUNT(DISTINCT Teacher_ID) FROM course_arrange
SELECT Name FROM teacher ORDER BY Age ASC
SELECT Name FROM teacher ORDER BY Age ASC
SELECT Age, Hometown FROM teacher
SELECT Age, Hometown FROM teacher
SELECT Name FROM teacher WHERE Hometown != 'Little Lever Urban District'
SELECT Name FROM teacher WHERE Hometown != 'Little Lever Urban District'
SELECT Name FROM teacher WHERE Age IN (32, 33)
SELECT Name FROM teacher WHERE Age IN ('32', '33')
SELECT Hometown FROM teacher WHERE Age = (SELECT MIN(Age) FROM teacher)
SELECT Hometown FROM teacher WHERE Age = (SELECT MIN(Age) FROM teacher)
SELECT Hometown, COUNT(*) FROM teacher GROUP BY Hometown
SELECT Hometown, COUNT(*) FROM teacher GROUP BY Hometown
SELECT Hometown FROM teacher GROUP BY Hometown ORDER BY COUNT(*) DESC LIMIT 1
SELECT Hometown FROM teacher GROUP BY Hometown ORDER BY COUNT(*) DESC LIMIT 1
SELECT Hometown FROM teacher GROUP BY Hometown HAVING COUNT(Teacher_ID) > 1
SELECT Hometown FROM teacher GROUP BY Hometown HAVING COUNT(Teacher_ID) >= 2
SELECT teacher.Name, course.Course FROM course_arrange JOIN teacher ON course_arrange.Teacher_ID = teacher.Teacher_ID JOIN course ON course_arrange.Course_ID = course.Course_ID
SELECT T2.Name, T3.Course FROM course_arrange AS T1 JOIN teacher AS T2 ON T1.Teacher_ID = T2.Teacher_ID JOIN course AS T3 ON T1.Course_ID = T3.Course_ID
SELECT teacher.Name, course.Course FROM course_arrange JOIN teacher ON course_arrange.Teacher_ID = teacher.Teacher_ID JOIN course ON course_arrange.Course_ID = course.Course_ID ORDER BY teacher.Name ASC
SELECT t.Name, c.Course FROM teacher t JOIN course_arrange ca ON t.Teacher_ID = ca.Teacher_ID JOIN course c ON ca.Course_ID = c.Course_ID ORDER BY t.Name ASC
SELECT T2.Name FROM course_arrange AS T1 JOIN teacher AS T2 ON T1.Teacher_ID = T2.Teacher_ID JOIN course AS T3 ON T1.Course_ID = T3.Course_ID WHERE T3.Course = 'math'
SELECT teacher.Name FROM teacher JOIN course_arrange ON teacher.Teacher_ID = course_arrange.Teacher_ID JOIN course ON course.Course_ID = course_arrange.Course_ID WHERE course.Course = 'math'
SELECT T2.Name, COUNT(T1.Course_ID) FROM course_arrange AS T1 JOIN teacher AS T2 ON T1.Teacher_ID = T2.Teacher_ID GROUP BY T2.Name
SELECT T2.Name, COUNT(T1.Course_ID) FROM course_arrange AS T1 JOIN teacher AS T2 ON T1.Teacher_ID = T2.Teacher_ID GROUP BY T2.Teacher_ID
SELECT t.Name FROM teacher t JOIN course_arrange ca ON t.Teacher_ID = ca.Teacher_ID GROUP BY t.Name HAVING COUNT(ca.Course_ID) >= 2
SELECT t.Name FROM teacher t JOIN course_arrange ca ON t.Teacher_ID = ca.Teacher_ID GROUP BY t.Name HAVING COUNT(ca.Course_ID) >= 2
SELECT Name FROM teacher WHERE Teacher_ID NOT IN (SELECT Teacher_ID FROM course_arrange)
SELECT Name FROM teacher WHERE Teacher_ID NOT IN (SELECT Teacher_ID FROM course_arrange)
SELECT COUNT(*) FROM visitor WHERE Age < 30
SELECT Name FROM visitor WHERE Level_of_membership > 4 ORDER BY Level_of_membership DESC
SELECT AVG(Age) FROM visitor WHERE Level_of_membership <= 4
SELECT Name, Level_of_membership FROM visitor WHERE Level_of_membership > 4 ORDER BY Age DESC
SELECT Museum_ID, Name FROM museum WHERE Num_of_Staff = (SELECT MAX(Num_of_Staff) FROM museum)
SELECT AVG(Num_of_Staff) FROM museum WHERE Open_Year < '2009'
SELECT Open_Year, Num_of_Staff FROM museum WHERE Name = 'Plaza Museum'
SELECT Name FROM museum WHERE Num_of_Staff > (SELECT MIN(Num_of_Staff) FROM museum WHERE Open_Year > '2010') AND Open_Year > '2010'
SELECT v.ID, v.Name, v.Age FROM visitor v JOIN visit vis ON v.ID = vis.visitor_ID GROUP BY v.ID, v.Name, v.Age HAVING COUNT(vis.Museum_ID) > 1
SELECT v.ID, v.Name, v.Level_of_membership FROM visitor v JOIN visit vi ON v.ID = vi.visitor_ID ORDER BY vi.Total_spent DESC LIMIT 1
SELECT T2.Museum_ID, T2.Name FROM visit AS T1 JOIN museum AS T2 ON T1.Museum_ID = T2.Museum_ID GROUP BY T1.Museum_ID ORDER BY COUNT(T1.Museum_ID) DESC LIMIT 1
SELECT Name FROM museum WHERE Museum_ID NOT IN (SELECT Museum_ID FROM visit)
SELECT v.Name, v.Age FROM visitor v JOIN visit vi ON v.ID = vi.visitor_ID WHERE vi.Num_of_Ticket = (SELECT MAX(Num_of_Ticket) FROM visit)
SELECT AVG(Num_of_Ticket) AS Avg_Tickets, MAX(Num_of_Ticket) AS Max_Tickets FROM visit
SELECT SUM(Total_spent) FROM visit WHERE visitor_ID IN (SELECT ID FROM visitor WHERE Level_of_membership = 1)
SELECT v.Name FROM visitor v JOIN visit vi ON v.ID = vi.visitor_ID JOIN museum m ON vi.Museum_ID = m.Museum_ID WHERE m.Open_Year < '2009' INTERSECT SELECT v.Name FROM visitor v JOIN visit vi ON v.ID = vi.visitor_ID JOIN museum m ON vi.Museum_ID = m.Museum_ID WHERE m.Open_Year > '2011'
SELECT COUNT(*) FROM visitor WHERE ID NOT IN (SELECT visitor_ID FROM visit WHERE Museum_ID IN (SELECT Museum_ID FROM museum WHERE Open_Year > '2010'))
SELECT COUNT(*) FROM museum WHERE Open_Year > '2013' OR Open_Year < '2008'
SELECT COUNT(*) FROM players
SELECT COUNT(*) FROM players
SELECT COUNT(*) FROM matches
SELECT COUNT(*) FROM matches
SELECT first_name, birth_date FROM players WHERE country_code = 'USA'
SELECT first_name, birth_date FROM players WHERE country_code = 'USA'
SELECT AVG(winner_age) AS avg_winner_age, AVG(loser_age) AS avg_loser_age FROM matches
SELECT AVG(winner_age) AS avg_winner_age, AVG(loser_age) AS avg_loser_age FROM matches
SELECT AVG(winner_rank) FROM matches WHERE winner_rank IS NOT NULL
SELECT AVG(winner_rank) FROM matches INNER JOIN players ON matches.winner_id = players.player_id
SELECT MAX(winner_rank) FROM matches WHERE loser_id IS NOT NULL
SELECT MIN(winner_rank) FROM matches WHERE winner_rank IS NOT NULL AND winner_rank > 0
SELECT COUNT(DISTINCT country_code) FROM players
SELECT COUNT(DISTINCT country_code) FROM players
SELECT COUNT(DISTINCT loser_name) FROM matches
SELECT COUNT(DISTINCT loser_name) FROM matches
SELECT DISTINCT t.tourney_name FROM matches m JOIN tourney t ON m.tourney_id = t.tourney_id GROUP BY t.tourney_name HAVING COUNT(m.match_num) > 10
SELECT DISTINCT t.tourney_name FROM matches m JOIN tourney t ON m.tourney_id = t.tourney_id GROUP BY t.tourney_name HAVING COUNT(m.match_num) > 10
SELECT DISTINCT p.first_name, p.last_name FROM players p JOIN matches m1 ON p.player_id = m1.winner_id JOIN matches m2 ON p.player_id = m2.winner_id WHERE m1.year = 2013 AND m2.year = 2016
SELECT DISTINCT p.first_name, p.last_name FROM players p JOIN matches m ON p.player_id = m.winner_id WHERE m.year = 2013 INTERSECT SELECT DISTINCT p.first_name, p.last_name FROM players p JOIN matches m ON p.player_id = m.winner_id WHERE m.year = 2016
SELECT COUNT(*) FROM matches WHERE year IN (2013, 2016)
SELECT COUNT(*) FROM matches WHERE year IN (2013, 2016)
SELECT p.country_code, p.first_name FROM players p JOIN matches m ON p.player_id = m.winner_id WHERE m.tourney_name IN ('WTA Championships', 'Australian Open') GROUP BY p.player_id HAVING COUNT(DISTINCT m.tourney_name) = 2
SELECT p.first_name, p.country_code FROM players p JOIN matches m ON p.player_id = m.winner_id WHERE m.tourney_name IN ('WTA Championships', 'Australian Open') GROUP BY p.player_id HAVING COUNT(DISTINCT m.tourney_name) = 2
SELECT first_name, country_code FROM players WHERE birth_date = (SELECT MIN(birth_date) FROM players)
SELECT first_name, country_code FROM players WHERE birth_date = (SELECT MIN(birth_date) FROM players)
SELECT first_name, last_name FROM players ORDER BY birth_date
SELECT first_name || ' ' || last_name AS full_name FROM players ORDER BY birth_date
SELECT first_name, last_name FROM players WHERE hand = 'L' ORDER BY birth_date
SELECT first_name, last_name FROM players WHERE hand = 'left' ORDER BY birth_date
SELECT p.first_name, p.country_code FROM rankings r JOIN players p ON r.player_id = p.player_id GROUP BY p.player_id ORDER BY SUM(r.tours) DESC LIMIT 1
SELECT p.first_name, p.country_code FROM players p JOIN rankings r ON p.player_id = r.player_id GROUP BY p.player_id ORDER BY SUM(r.tours) DESC LIMIT 1
SELECT year FROM matches GROUP BY year ORDER BY COUNT(*) DESC LIMIT 1
SELECT year FROM matches GROUP BY year ORDER BY COUNT(*) DESC LIMIT 1
SELECT p.first_name, p.last_name, r.ranking_points FROM players p JOIN ( SELECT winner_id FROM matches GROUP BY winner_id ORDER BY COUNT(*) DESC LIMIT 1 ) m ON p.player_id = m.winner_id JOIN rankings r ON p.player_id = r.player_id
SELECT p.first_name, p.last_name, r.ranking_points FROM players p JOIN ( SELECT winner_id FROM matches GROUP BY winner_id ORDER BY COUNT(*) DESC LIMIT 1 ) m ON p.player_id = m.winner_id JOIN rankings r ON p.player_id = r.player_id
SELECT p.winner_name FROM matches m JOIN players p ON m.winner_id = p.player_id WHERE m.tourney_name = 'Australian Open' AND p.player_id = (SELECT winner_id FROM matches WHERE winner_id = p.player_id ORDER BY winner_rank_points DESC LIMIT 1)
SELECT p.winner_name FROM matches m JOIN players p ON m.winner_id = p.player_id JOIN rankings r ON p.player_id = r.player_id WHERE m.tourney_name = 'Australian Open' ORDER BY r.ranking_points DESC LIMIT 1
SELECT winner_name, loser_name FROM matches WHERE minutes = (SELECT MAX(minutes) FROM matches)
SELECT p1.winner_name AS winner_name, p2.loser_name AS loser_name FROM matches JOIN players p1 ON matches.winner_id = p1.player_id JOIN players p2 ON matches.loser_id = p2.player_id ORDER BY matches.minutes DESC LIMIT 1
SELECT p.first_name, AVG(r.ranking) AS avg_ranking FROM players p JOIN rankings r ON p.player_id = r.player_id GROUP BY p.player_id, p.first_name
SELECT p.first_name, AVG(r.ranking) AS average_ranking FROM players p JOIN rankings r ON p.player_id = r.player_id GROUP BY p.player_id, p.first_name
SELECT p.first_name, SUM(r.ranking_points) AS total_ranking_points FROM players p JOIN rankings r ON p.player_id = r.player_id GROUP BY p.player_id, p.first_name
SELECT p.first_name, SUM(r.ranking_points) AS total_ranking_points FROM players p JOIN rankings r ON p.player_id = r.player_id GROUP BY p.player_id, p.first_name
SELECT country_code, COUNT(*) AS number_of_players FROM players GROUP BY country_code
SELECT country_code, COUNT(*) FROM players GROUP BY country_code
SELECT country_code FROM players GROUP BY country_code ORDER BY COUNT(*) DESC LIMIT 1
SELECT country_code FROM players GROUP BY country_code ORDER BY COUNT(*) DESC LIMIT 1
SELECT country_code FROM players GROUP BY country_code HAVING COUNT(*) > 50
SELECT DISTINCT country_code FROM players GROUP BY country_code HAVING COUNT(*) > 50
SELECT ranking_date, COUNT(DISTINCT player_id) AS total_tours FROM rankings GROUP BY ranking_date
SELECT ranking_date, COUNT(ranking) AS total_tours FROM rankings GROUP BY ranking_date
SELECT year, COUNT(*) AS matches_count FROM matches GROUP BY year
SELECT year, COUNT(*) FROM matches GROUP BY year
SELECT p.first_name, p.last_name, p.player_id, r.ranking FROM players p JOIN matches m ON p.player_id = m.winner_id JOIN rankings r ON p.player_id = r.player_id WHERE r.ranking_points IS NOT NULL ORDER BY m.winner_age ASC LIMIT 3
SELECT p.first_name, p.last_name, r.ranking FROM players p JOIN matches m ON p.player_id = m.winner_id JOIN rankings r ON r.player_id = p.player_id WHERE r.ranking_points IS NOT NULL ORDER BY m.winner_age ASC LIMIT 3
SELECT COUNT(DISTINCT winner_id) FROM matches JOIN players ON matches.winner_id = players.player_id WHERE players.hand = 'left' AND tourney_name = 'WTA Championships'
SELECT COUNT(*) FROM matches INNER JOIN players ON matches.winner_id = players.player_id WHERE players.hand = 'left' AND tourney_name = 'WTA Championships'
SELECT p.first_name, p.country_code, p.birth_date FROM players p JOIN matches m ON p.player_id = m.winner_id JOIN rankings r ON p.player_id = r.player_id WHERE r.ranking_points = (SELECT MAX(ranking_points) FROM rankings)
SELECT p.first_name, p.country_code, p.birth_date FROM players p JOIN ( SELECT winner_id FROM matches GROUP BY winner_id ORDER BY SUM(winner_rank_points) DESC LIMIT 1 ) m ON p.player_id = m.winner_id
SELECT hand, COUNT(*) AS number_of_players FROM players GROUP BY hand
SELECT hand, COUNT(*) FROM players GROUP BY hand
SELECT COUNT(*) FROM ship WHERE disposition_of_ship = 'Captured'
SELECT name, tonnage FROM ship ORDER BY name DESC
SELECT name, date, result FROM battle
SELECT MIN(killed + injured) AS min_toll, MAX(killed + injured) AS max_toll FROM death
SELECT AVG(injured) FROM death
SELECT d.note, SUM(d.killed), SUM(d.injured) FROM death d JOIN ship s ON d.caused_by_ship_id = s.id WHERE s.tonnage = 't' GROUP BY d.note
SELECT name, result FROM battle WHERE bulgarian_commander NOT LIKE 'Boril'
SELECT DISTINCT b.id, b.name FROM battle b JOIN ship s ON b.id = s.lost_in_battle WHERE s.ship_type = 'Brig'
SELECT battle.id, battle.name FROM battle JOIN death ON battle.id = death.caused_by_ship_id GROUP BY battle.id, battle.name HAVING SUM(death.killed) > 10
SELECT ship.id, ship.name FROM ship JOIN death ON ship.id = death.caused_by_ship_id GROUP BY ship.id, ship.name ORDER BY SUM(death.injured) DESC LIMIT 1
SELECT DISTINCT name FROM battle WHERE bulgarian_commander = 'Kaloyan' AND latin_commander = 'Baldwin I'
SELECT COUNT(DISTINCT result) FROM battle
SELECT COUNT(*) FROM battle WHERE id NOT IN (SELECT lost_in_battle FROM ship WHERE tonnage = '225')
SELECT b.name, b.date FROM battle b JOIN ship s1 ON b.id = s1.lost_in_battle JOIN ship s2 ON b.id = s2.lost_in_battle JOIN death d ON s1.id = d.caused_by_ship_id WHERE s1.name = 'Lettice' AND s2.name = 'HMS Atalanta'
SELECT b.name, b.result, b.bulgarian_commander FROM battle b JOIN ship s ON b.id = s.lost_in_battle WHERE s.lost_in_battle IS NULL AND b.location = 'English Channel'
SELECT note FROM death WHERE note LIKE '%East%'
SELECT line_1, line_2 FROM Addresses WHERE line_1 IS NOT NULL OR line_2 IS NOT NULL
SELECT line_1, line_2 FROM Addresses
SELECT COUNT(*) FROM Courses
SELECT COUNT(*) FROM Courses
SELECT course_description FROM Courses WHERE course_name = 'Math'
SELECT course_description FROM Courses WHERE course_name LIKE '%Math%'
SELECT zip_postcode FROM Addresses WHERE city = 'Port Chelsea'
SELECT zip_postcode FROM Addresses WHERE city = 'Port Chelsea'
SELECT D.department_name, D.department_id FROM Degree_Programs DP JOIN Departments D ON DP.department_id = D.department_id GROUP BY D.department_id, D.department_name ORDER BY COUNT(DP.degree_program_id) DESC LIMIT 1
SELECT department_id, department_name FROM Departments WHERE department_id = (SELECT department_id FROM Degree_Programs GROUP BY department_id ORDER BY COUNT(degree_summary_name) DESC LIMIT 1)
SELECT COUNT(DISTINCT department_id) FROM Degree_Programs
SELECT COUNT(DISTINCT department_id) FROM Degree_Programs
SELECT COUNT(DISTINCT degree_summary_name) FROM Degree_Programs
SELECT COUNT(DISTINCT degree_summary_name) FROM Degree_Programs
SELECT COUNT(*) FROM Degree_Programs WHERE department_id = (SELECT department_id FROM Departments WHERE department_name = 'Engineering')
SELECT COUNT(*) FROM Degree_Programs WHERE department_id = (SELECT department_id FROM Departments WHERE department_name = 'Engineering')
SELECT section_name, section_description FROM Sections
SELECT section_name, section_description FROM Sections
SELECT course_id, course_name FROM Courses WHERE course_id IN (SELECT course_id FROM Sections GROUP BY course_id HAVING COUNT(section_id) <= 2)
SELECT course_id, course_name FROM Courses WHERE course_id NOT IN (SELECT course_id FROM Sections GROUP BY course_id HAVING COUNT(section_id) >= 2)
SELECT section_name FROM Sections ORDER BY section_name DESC
SELECT section_name FROM Sections ORDER BY section_name DESC
SELECT S.semester_id, T.semester_name FROM Semesters T JOIN Student_Enrolment E ON T.semester_id = E.semester_id GROUP BY S.semester_id, T.semester_name ORDER BY COUNT(E.student_id) DESC LIMIT 1
SELECT S.semester_id, S.semester_name FROM Semesters S JOIN Student_Enrolment E ON S.semester_id = E.semester_id GROUP BY S.semester_id, S.semester_name HAVING COUNT(E.student_id) = ( SELECT COUNT(student_id) FROM Student_Enrolment GROUP BY semester_id ORDER BY COUNT(student_id) DESC LIMIT 1 )
SELECT department_description FROM Departments WHERE department_name LIKE '%the computer%'
SELECT department_description FROM Departments WHERE department_name LIKE '%computer%'
SELECT DISTINCT s.first_name, s.middle_name, s.last_name, s.student_id FROM Students s JOIN Student_Enrolment se ON s.student_id = se.student_id WHERE (SELECT COUNT(*) FROM Student_Enrolment se2 WHERE se2.student_id = s.student_id) = 2 AND se.semester_id = (SELECT se3.semester_id FROM Student_Enrolment se3 WHERE se3.student_id = s.student_id LIMIT 1)
SELECT s.student_id, s.first_name, s.middle_name, s.last_name FROM Students s JOIN Student_Enrolment se ON s.student_id = se.student_id WHERE (SELECT COUNT(*) FROM Student_Enrolment se2 WHERE se2.student_id = s.student_id AND se2.semester_id = se.semester_id AND se2.degree_program_id = se.degree_program_id) = 2
SELECT first_name, middle_name, last_name FROM Students WHERE student_id IN (SELECT student_id FROM Student_Enrolment WHERE degree_program_id IN (SELECT degree_program_id FROM Degree_Programs WHERE degree_summary_name LIKE 'Bachelor%'))
SELECT DISTINCT s.first_name, s.middle_name, s.last_name FROM Students s JOIN Student_Enrolment e ON s.student_id = e.student_id JOIN Degree_Programs dp ON e.degree_program_id = dp.degree_program_id WHERE dp.degree_summary_name = 'Bachelors'
SELECT Degree_Programs.degree_summary_name FROM Degree_Programs JOIN Student_Enrolment ON Degree_Programs.degree_program_id = Student_Enrolment.degree_program_id GROUP BY Degree_Programs.degree_summary_name ORDER BY COUNT(*) DESC LIMIT 1
SELECT dp.degree_summary_name FROM Degree_Programs dp JOIN Student_Enrolment se ON dp.degree_program_id = se.degree_program_id GROUP BY dp.degree_program_id, dp.degree_summary_name ORDER BY COUNT(se.student_id) DESC LIMIT 1
SELECT degree_program_id, degree_summary_name FROM Degree_Programs WHERE degree_program_id = (SELECT degree_program_id FROM Student_Enrolment GROUP BY degree_program_id ORDER BY COUNT(student_id) DESC LIMIT 1)
SELECT dp.degree_program_id, dp.degree_summary_name FROM Degree_Programs dp JOIN Student_Enrolment se ON dp.degree_program_id = se.degree_program_id GROUP BY dp.degree_program_id, dp.degree_summary_name ORDER BY COUNT(se.student_id) DESC LIMIT 1
SELECT s.student_id, s.first_name, s.middle_name, s.last_name, COUNT(se.student_enrolment_id) AS num_enrollments, se.student_id AS enrolment_student_id FROM Students s JOIN Student_Enrolment se ON s.student_id = se.student_id GROUP BY s.student_id, s.first_name, s.middle_name, s.last_name, se.student_id ORDER BY num_enrollments DESC LIMIT 1
SELECT s.student_id, s.first_name, s.middle_name, s.last_name, COUNT(se.student_enrolment_id) AS num_enrollments FROM Students s JOIN Student_Enrolment se ON s.student_id = se.student_id GROUP BY s.student_id ORDER BY num_enrollments DESC LIMIT 1
SELECT semester_name FROM Semesters WHERE semester_id NOT IN (SELECT semester_id FROM Student_Enrolment)
SELECT semester_name FROM Semesters WHERE semester_id NOT IN (SELECT semester_id FROM Student_Enrolment)
SELECT DISTINCT C.course_name FROM Courses C JOIN Student_Enrolment_Courses SEC ON C.course_id = SEC.course_id JOIN Student_Enrolment SE ON SEC.student_enrolment_id = SE.student_enrolment_id
SELECT DISTINCT c.course_name FROM Courses c JOIN Student_Enrolment_Courses sec ON c.course_id = sec.course_id JOIN Student_Enrolment se ON sec.student_enrolment_id = se.student_enrolment_id
SELECT C.course_name FROM Courses C JOIN Student_Enrolment_Courses SEC ON C.course_id = SEC.course_id JOIN Student_Enrolment SE ON SEC.student_enrolment_id = SE.student_enrolment_id GROUP BY C.course_name ORDER BY COUNT(*) DESC LIMIT 1
SELECT C.course_name FROM Courses C JOIN Sections S ON C.course_id = S.course_id JOIN Student_Enrolment_Courses SEC ON S.section_id = SEC.course_id GROUP BY C.course_name ORDER BY COUNT(SEC.student_course_id) DESC LIMIT 1
SELECT last_name FROM Students WHERE current_address_id IN (SELECT address_id FROM Addresses WHERE state_province_county = 'North Carolina') AND student_id NOT IN (SELECT student_id FROM Student_Enrolment)
SELECT DISTINCT s.last_name FROM Students s JOIN Addresses a ON s.current_address_id = a.address_id OR s.permanent_address_id = a.address_id WHERE a.state_province_county = 'North Carolina' AND s.student_id NOT IN (SELECT student_id FROM Student_Enrolment)
SELECT T1.transcript_id, T1.transcript_date FROM Transcripts AS T1 JOIN Transcript_Contents AS T2 ON T1.transcript_id = T2.transcript_id GROUP BY T1.transcript_id, T1.transcript_date HAVING COUNT(T2.student_course_id) >= 2
SELECT T1.transcript_id, T1.transcript_date FROM Transcripts AS T1 JOIN Transcript_Contents AS T2 ON T1.transcript_id = T2.transcript_id GROUP BY T1.transcript_id, T1.transcript_date HAVING COUNT(T2.student_course_id) >= 2
SELECT cell_mobile_number FROM Students WHERE first_name = 'Timmothy' AND last_name = 'Ward' AND cell_mobile_number IS NOT NULL
SELECT cell_mobile_number FROM Students WHERE first_name = 'Timmothy' AND last_name = 'Ward'
SELECT first_name, middle_name, last_name FROM Students WHERE date_first_registered = (SELECT MIN(date_first_registered) FROM Students)
SELECT first_name, middle_name, last_name FROM Students WHERE date_first_registered = (SELECT MIN(date_first_registered) FROM Students)
SELECT first_name, middle_name, last_name FROM Students WHERE date_left = (SELECT MIN(date_left) FROM Students WHERE date_left IS NOT NULL)
SELECT first_name, middle_name, last_name FROM Students WHERE date_left = (SELECT MIN(date_left) FROM Students)
SELECT first_name FROM Students WHERE permanent_address_id != current_address_id
SELECT first_name FROM Students WHERE permanent_address_id != current_address_id
SELECT a.address_id, a.line_1, a.line_2, a.line_3 FROM Addresses a JOIN Students s ON a.address_id = s.current_address_id GROUP BY a.address_id, a.line_1, a.line_2, a.line_3 ORDER BY COUNT(s.student_id) DESC LIMIT 1
SELECT address_id, line_1, line_2 FROM Addresses WHERE address_id = (SELECT current_address_id FROM Students GROUP BY current_address_id ORDER BY COUNT(*) DESC LIMIT 1)
SELECT AVG(tran.transcript_date) FROM Transcripts tran
SELECT AVG(transcript_date) AS average_transcript_date FROM Transcripts
SELECT MIN(tr.transcript_date) AS first_transcript_date, tr.other_details FROM Transcripts tr GROUP BY tr.other_details
SELECT MIN(transcript_date), other_details FROM Transcripts GROUP BY other_details
SELECT COUNT(*) FROM Transcripts
SELECT COUNT(*) FROM Transcripts
SELECT MAX(transcript_date) FROM Transcripts
SELECT transcript_date FROM Transcripts ORDER BY transcript_date DESC LIMIT 1
SELECT MAX(COUNT(DISTINCT t.transcript_id)), sc.student_course_id FROM Student_Enrolment_Courses sc JOIN Transcript_Contents tc ON sc.student_course_id = tc.student_course_id JOIN Transcripts t ON tc.transcript_id = t.transcript_id GROUP BY sc.student_course_id
SELECT MAX(T2.student_course_id) AS max_student_course_id, T1.course_id AS max_course_id FROM Student_Enrolment_Courses T1 JOIN (SELECT course_id, COUNT(*) AS course_count FROM Student_Enrolment_Courses GROUP BY course_id) T2 ON T1.course_id = T2.course_id GROUP BY T1.course_id ORDER BY course_count DESC LIMIT 1
SELECT T1.transcript_id, T1.transcript_date FROM Transcripts AS T1 JOIN (SELECT transcript_id, COUNT(*) AS cnt FROM Transcript_Contents GROUP BY transcript_id ORDER BY cnt ASC LIMIT 1) AS T2 ON T1.transcript_id = T2.transcript_id
SELECT T1.transcript_id, T1.transcript_date FROM Transcripts AS T1 JOIN Transcript_Contents AS T2 ON T1.transcript_id = T2.transcript_id GROUP BY T1.transcript_id, T1.transcript_date ORDER BY COUNT(T2.student_course_id) ASC LIMIT 1
SELECT S2.semester_id, S2.semester_name FROM Semesters S2 JOIN Student_Enrolment S1 ON S2.semester_id = S1.semester_id WHERE EXISTS (SELECT 1 FROM Degree_Programs WHERE degree_program_id = S1.degree_program_id AND degree_summary_name LIKE '%Master%') AND EXISTS (SELECT 1 FROM Degree_Programs WHERE degree_program_id = S1.degree_program_id AND degree_summary_name LIKE '%Bachelor%')
SELECT semester_id FROM Student_Enrolment WHERE degree_program_id IN (SELECT degree_program_id FROM Degree_Programs WHERE degree_summary_name IN ('Masters', 'Bachelors')) GROUP BY semester_id HAVING COUNT(DISTINCT degree_program_id) = 2
SELECT COUNT(DISTINCT current_address_id) FROM Students WHERE current_address_id IS NOT NULL
SELECT DISTINCT a1.line_1, a1.line_2, a1.line_3, a1.city, a1.zip_postcode, a1.state_province_county, a1.country FROM Addresses a1 INNER JOIN Students s ON a1.address_id = s.current_address_id OR a1.address_id = s.permanent_address_id
SELECT first_name, middle_name, last_name, cell_mobile_number, email_address, ssn, date_first_registered, date_left, other_student_details FROM Students ORDER BY last_name DESC, first_name DESC, middle_name DESC
SELECT other_student_details FROM Students ORDER BY last_name DESC, first_name DESC
SELECT S.first_name, S.last_name, C.course_name, Se.section_name, D.degree_summary_name, Sm.semester_name FROM Students S JOIN Student_Enrolment Se ON S.student_id = Se.student_id JOIN Degree_Programs D ON Se.degree_program_id = D.degree_program_id JOIN Semesters Sm ON Se.semester_id = Sm.semester_id JOIN Student_Enrolment_Courses SC ON Se.student_enrolment_id = SC.student_enrolment_id JOIN Courses C ON SC.course_id = C.course_id
SELECT S.section_description FROM Sections S JOIN Courses C ON S.course_id = C.course_id WHERE S.section_name = 'h'
SELECT first_name FROM Students WHERE permanent_address_id IN (SELECT address_id FROM Addresses WHERE country = 'Haiti') OR cell_mobile_number = '09700166582'
SELECT DISTINCT s.first_name FROM Students s WHERE s.permanent_address_id IN (SELECT address_id FROM Addresses WHERE country = 'Haiti') OR s.cell_mobile_number = '09700166582'
SELECT Title FROM Cartoon ORDER BY Title ASC
SELECT Title FROM Cartoon ORDER BY Title ASC
SELECT Title FROM Cartoon WHERE Directed_by = "Ben Jones"
SELECT Title FROM Cartoon WHERE Directed_by = 'Ben Jones'
SELECT COUNT(*) FROM Cartoon WHERE Written_by = "Joseph Kuhr"
SELECT COUNT(*) FROM Cartoon WHERE Written_by = 'Joseph Kuhr'
SELECT Title, Directed_by FROM Cartoon ORDER BY Original_air_date
SELECT C.Title, CDirected_by FROM Cartoon C JOIN TV_Channel TC ON C.Channel = TC.id ORDER BY C.Original_air_date
SELECT Title FROM Cartoon WHERE Directed_by = "Ben Jones" OR Directed_by = "Brandon Vietti"
SELECT Title FROM Cartoon WHERE Directed_by = 'Ben Jones' OR Directed_by = 'Brandon Vietti'
SELECT Country, COUNT(*) AS Num_Channels FROM TV_Channel GROUP BY Country ORDER BY Num_Channels DESC LIMIT 1
SELECT Country, COUNT(*) AS Channel_Count FROM TV_Channel GROUP BY Country ORDER BY Channel_Count DESC LIMIT 1
SELECT COUNT(DISTINCT series_name, Content) FROM TV_Channel
SELECT COUNT(DISTINCT series_name, Content) FROM TV_Channel
SELECT Content FROM TV_Channel WHERE series_name = "Sky Radio"
SELECT Content FROM TV_Channel WHERE series_name = 'Sky Radio'
SELECT Package_Option FROM TV_Channel WHERE series_name = "Sky Radio"
SELECT Package_Option FROM TV_Channel WHERE series_name = 'Sky Radio'
SELECT COUNT(*) FROM TV_Channel WHERE Language = 'English'
SELECT COUNT(*) FROM TV_Channel WHERE Language = 'English'
SELECT Language, COUNT(*) AS Channel_Count FROM TV_Channel GROUP BY Language ORDER BY Channel_Count ASC LIMIT 1
SELECT Language, COUNT(*) AS Num_Channels FROM TV_Channel GROUP BY Language ORDER BY Num_Channels ASC LIMIT 1
SELECT Language, COUNT(*) FROM TV_Channel GROUP BY Language
SELECT Language, COUNT(*) FROM TV_Channel GROUP BY Language
SELECT TV_Channel.series_name FROM TV_Channel JOIN Cartoon ON TV_Channel.id = Cartoon.Channel WHERE Cartoon.Title = 'The Rise of the Blue Beetle!'
SELECT TV_Channel.series_name FROM TV_Channel JOIN Cartoon ON TV_Channel.id = Cartoon.Channel WHERE Cartoon.Title = 'The Rise of the Blue Beetle'
SELECT C.Title FROM Cartoon C JOIN TV_Channel TC ON C.Channel = TC.id WHERE TC.series_name = 'Sky Radio'
SELECT C.Title FROM Cartoon C JOIN TV_Channel TC ON C.Channel = TC.id WHERE TC.series_name = "Sky Radio"
SELECT Episode FROM TV_series ORDER BY Rating
SELECT Episode FROM TV_series ORDER BY Rating DESC
SELECT Episode, Rating FROM TV_series ORDER BY Rating DESC LIMIT 3
SELECT Episode, Rating FROM TV_series ORDER BY Rating DESC LIMIT 3
SELECT min(Share), max(Share) FROM TV_series
SELECT min(Share) AS Min_Share, max(Share) AS Max_Share FROM TV_series
SELECT Air_Date FROM TV_series WHERE Episode = "A Love of a Lifetime"
SELECT Air_Date FROM TV_series WHERE Episode = 'A Love of a Lifetime'
SELECT Weekly_Rank FROM TV_series WHERE Episode = "A Love of a Lifetime"
SELECT Weekly_Rank FROM TV_series WHERE Episode = 'A Love of a Lifetime'
SELECT T2.series_name FROM TV_series AS T1 JOIN TV_Channel AS T2 ON T1.Channel = T2.id WHERE T1.Episode = 'A Love of a Lifetime'
SELECT T2.series_name FROM TV_series AS T1 JOIN TV_Channel AS T2 ON T1.Channel = T2.id WHERE T1.Episode = 'A Love of a Lifetime'
SELECT T2.Episode FROM TV_Channel AS T1 JOIN TV_series AS T2 ON T1.id = T2.Channel WHERE T1.series_name = 'Sky Radio'
SELECT Episode FROM TV_series WHERE Channel = (SELECT id FROM TV_Channel WHERE series_name = "Sky Radio")
SELECT Directed_by, COUNT(*) FROM Cartoon GROUP BY Directed_by
SELECT Directed_by, COUNT(*) FROM Cartoon GROUP BY Directed_by
SELECT Production_code, Channel FROM Cartoon WHERE Original_air_date = (SELECT MAX(Original_air_date) FROM Cartoon)
SELECT Production_code, Channel FROM Cartoon WHERE Original_air_date = (SELECT MAX(Original_air_date) FROM Cartoon)
SELECT Package_Option, series_name FROM TV_Channel WHERE Hight_definition_TV = 'YES'
SELECT Package_Option, series_name FROM TV_Channel WHERE Hight_definition_TV = 'yes'
SELECT T3.Country FROM Cartoon AS T1 JOIN TV_Channel AS T3 ON T1.Channel = T3.id JOIN TV_Series AS T2 ON T1.Channel = T2.Channel WHERE T1.Written_by = 'Todd Casey'
SELECT T1.Country FROM TV_Channel AS T1 JOIN Cartoon AS T2 ON T1.id = T2.Channel WHERE T2.Written_by = 'Todd Casey'
SELECT T1.Country FROM TV_Channel AS T1 JOIN Cartoon AS T2 ON T1.id = T2.Channel WHERE T2.Written_by != 'Todd Casey'
SELECT DISTINCT T1.Country FROM TV_Channel AS T1 JOIN Cartoon AS T2 ON T1.id = T2.Channel WHERE T2.Written_by NOT LIKE '%Todd Casey%'
SELECT T1.series_name, T1.Country FROM TV_Channel AS T1 JOIN Cartoon AS T2 ON T1.id = T2.Channel WHERE T2Directed_by = 'Ben Jones' AND T2Directed_by = 'Michael Chang'
SELECT T1.series_name, T1.Country FROM TV_Channel AS T1 JOIN Cartoon AS T2 ON T1.id = T2.Channel WHERE T2Directed_by = 'Ben Jones' UNION SELECT T1.series_name, T1.Country FROM TV_Channel AS T1 JOIN Cartoon AS T2 ON T1.id = T2.Channel WHERE T2Directed_by = 'Michael Chang'
SELECT Pixel_aspect_ratio_PAR, Country FROM TV_Channel WHERE Language != 'English'
SELECT Pixel_aspect_ratio_PAR, Country FROM TV_Channel WHERE Language != 'English'
SELECT id FROM TV_Channel WHERE Country IN (SELECT Country FROM TV_Channel GROUP BY Country HAVING COUNT(id) > 2)
SELECT id FROM TV_Channel WHERE id IN (SELECT Channel FROM TV_series GROUP BY Channel HAVING COUNT(*) > 2) UNION SELECT Channel FROM Cartoon WHERE Channel IN (SELECT Channel FROM TV_series GROUP BY Channel HAVING COUNT(*) > 2)
SELECT id FROM TV_Channel WHERE id NOT IN (SELECT Channel FROM Cartoon WHERE Directed_by = 'Ben Jones')
SELECT id FROM TV_Channel WHERE id NOT IN (SELECT Channel FROM Cartoon WHERE Directed_by = 'Ben Jones')
SELECT T1.Package_Option FROM TV_Channel AS T1 LEFT JOIN Cartoon AS T2 ON T1.id = T2.Channel WHERE T2Directed_by != 'Ben Jones' AND T2.Channel IS NOT NULL GROUP BY T1.id HAVING COUNT(T2.Channel) = 0
SELECT DISTINCT T1.Package_Option FROM TV_Channel AS T1 JOIN TV_series AS T2 ON T1.id = T2.Channel WHERE T2.Channel NOT IN (SELECT Channel FROM Cartoon WHERE Directed_by = 'Ben Jones')
SELECT COUNT(*) FROM poker_player
SELECT COUNT(Poker_Player_ID) FROM poker_player
SELECT Earnings FROM poker_player ORDER BY Earnings DESC
SELECT Earnings FROM poker_player ORDER BY Earnings DESC
SELECT Final_Table_Made, Best_Finish FROM poker_player
SELECT Final_Table_Made, Best_Finish FROM poker_player
SELECT AVG(Earnings) FROM poker_player
SELECT AVG(Earnings) FROM poker_player
SELECT Money_Rank FROM poker_player WHERE Earnings = (SELECT MAX(Earnings) FROM poker_player)
SELECT Money_Rank FROM poker_player WHERE Earnings = (SELECT MAX(Earnings) FROM poker_player)
SELECT MAX(Final_Table_Made) FROM poker_player WHERE Earnings < 200000
SELECT MAX(Final_Table_Made) FROM poker_player WHERE Earnings < 200000
SELECT Name FROM people
SELECT Name FROM people WHERE People_ID IN (SELECT People_ID FROM poker_player)
SELECT T2.Name FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID = T2.People_ID WHERE T1.Earnings > 300000
SELECT p.Name FROM people p JOIN poker_player pp ON p.People_ID = pp.People_ID WHERE pp.Earnings > 300000
SELECT T2.Name FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID = T2.People_ID ORDER BY T1.Final_Table_Made ASC
SELECT T2.Name FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID = T2.People_ID ORDER BY T1.Final_Table_Made ASC
SELECT T2.Birth_Date FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID = T2.People_ID WHERE T1.Earnings = (SELECT MIN(Earnings) FROM poker_player)
SELECT Birth_Date FROM people WHERE People_ID = (SELECT People_ID FROM poker_player ORDER BY Earnings ASC LIMIT 1)
SELECT poker_player.Money_Rank FROM poker_player JOIN people ON poker_player.People_ID = people.People_ID ORDER BY people.Height DESC LIMIT 1
SELECT T2.Money_Rank FROM people AS T1 JOIN poker_player AS T2 ON T1.People_ID = T2.People_ID WHERE T1.Height = (SELECT MAX(Height) FROM people)
SELECT AVG(T1.Earnings) FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID = T2.People_ID WHERE T2.Height > 200
SELECT AVG(T1.Earnings) FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID = T2.People_ID WHERE T2.Height > 200
SELECT T2.Name FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID = T2.People_ID ORDER BY T1.Earnings DESC
SELECT p.Name FROM people p JOIN poker_player pp ON p.People_ID = pp.People_ID ORDER BY pp.Earnings DESC
SELECT Nationality, COUNT(*) FROM people GROUP BY Nationality
SELECT Nationality, COUNT(*) FROM people GROUP BY Nationality
SELECT Nationality FROM people GROUP BY Nationality ORDER BY COUNT(*) DESC LIMIT 1
SELECT Nationality FROM people GROUP BY Nationality ORDER BY COUNT(*) DESC LIMIT 1
SELECT Nationality FROM people GROUP BY Nationality HAVING COUNT(*) > 1
SELECT Nationality FROM people GROUP BY Nationality HAVING COUNT(*) >= 2
SELECT Name, Birth_Date FROM people ORDER BY Name ASC
SELECT Name, Birth_Date FROM people ORDER BY Name
SELECT p.Name FROM people p JOIN poker_player pp ON p.People_ID = pp.People_ID WHERE p.Nationality != 'Russia'
SELECT Name FROM people WHERE Nationality != 'Russia'
SELECT Name FROM people WHERE People_ID NOT IN (SELECT People_ID FROM poker_player)
SELECT Name FROM people WHERE People_ID NOT IN (SELECT People_ID FROM poker_player)
SELECT COUNT(DISTINCT Nationality) FROM people
SELECT COUNT(DISTINCT Nationality) FROM people
SELECT COUNT(DISTINCT state) FROM AREA_CODE_STATE
SELECT C.contestant_number, C.contestant_name FROM CONTESTANTS C ORDER BY C.contestant_name DESC
SELECT VOTE_ID, PHONE_NUMBER, STATE FROM VOTES
SELECT MIN(area_code), MAX(area_code) FROM AREA_CODE_STATE
SELECT MAX(created) FROM VOTES WHERE state = 'CA'
SELECT contestant_name FROM CONTESTANTS WHERE contestant_name != 'Jessie Alloway'
SELECT DISTINCT state, created FROM VOTES
SELECT C.contestant_number, C.contestant_name FROM CONTESTANTS C JOIN VOTES V ON C.contestant_number = V.contestant_number GROUP BY C.contestant_number, C.contestant_name HAVING COUNT(V.vote_id) >= 2
SELECT C.contestant_number, C.contestant_name FROM CONTESTANTS C JOIN VOTES V ON C.contestant_number = V.contestant_number GROUP BY C.contestant_number, C.contestant_name HAVING MIN(V.vote_id)
SELECT COUNT(*) FROM VOTES WHERE state IN ('NY', 'CA')
SELECT COUNT(*) FROM CONTESTANTS WHERE contestant_number NOT IN (SELECT contestant_number FROM VOTES)
SELECT T2.area_code FROM VOTES AS T1 JOIN AREA_CODE_STATE AS T2 ON T1.state = T2.state GROUP BY T2.area_code ORDER BY COUNT(T1.vote_id) DESC LIMIT 1
SELECT VOTES.created, VOTES.state, VOTES.phone_number FROM VOTES JOIN CONTESTANTS ON VOTES.contestant_number = CONTESTANTS.contestant_number WHERE CONTESTANTS.contestant_name = 'Tabatha Gehling'
SELECT DISTINCT v1.phone_number.area_code FROM VOTES v1 JOIN CONTESTANTS c1 ON v1.contestant_number = c1.contestant_number JOIN AREA_CODE_STATE a1 ON v1.state = a1.state JOIN VOTES v2 ON v1.phone_number = v2.phone_number AND v1.state = v2.state AND v1.created = v2.created JOIN CONTESTANTS c2 ON v2.contestant_number = c2.contestant_number JOIN AREA_CODE_STATE a2 ON v2.state = a2.state WHERE c1.contestant_name = 'Tabatha Gehling' AND c2.contestant_name = 'Kelly Clauss'
SELECT contestant_name FROM CONTESTANTS WHERE contestant_name LIKE '%Al%'
SELECT Name FROM country WHERE IndepYear > 1950
SELECT Name FROM country WHERE IndepYear > 1950
SELECT COUNT(*) FROM country WHERE GovernmentForm = 'Republic'
SELECT COUNT(*) FROM country WHERE GovernmentForm = 'Republic'
SELECT SUM(SurfaceArea) FROM country WHERE Region = 'Caribbean'
SELECT SUM(SurfaceArea) FROM country WHERE Region = 'Caribbean'
SELECT Continent FROM country WHERE Name = 'Anguilla'
SELECT Continent FROM country WHERE Name = 'Anguilla'
SELECT T2.Region FROM city AS T1 JOIN country AS T2 ON T1.CountryCode = T2.Code WHERE T1.Name = 'Kabul'
SELECT T2.Region FROM city AS T1 JOIN country AS T2 ON T1.CountryCode = T2.Code WHERE T1.Name = 'Kabul'
SELECT T2.Language FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code = T2.CountryCode WHERE T1.Code = 'ABW' ORDER BY T2.Percentage DESC LIMIT 1
SELECT Language FROM countrylanguage WHERE CountryCode = (SELECT Code FROM country WHERE Name = 'Aruba') AND IsOfficial = 'T' AND Percentage = (SELECT MAX(Percentage) FROM countrylanguage WHERE CountryCode = (SELECT Code FROM country WHERE Name = 'Aruba'))
SELECT Population, LifeExpectancy FROM country WHERE Name = 'Brazil'
SELECT Population, LifeExpectancy FROM country WHERE Name = 'Brazil'
SELECT Region, Population FROM country WHERE Name = 'Angola'
SELECT Region, Population FROM country WHERE Name = 'Angola'
SELECT AVG(LifeExpectancy) FROM country WHERE Region = 'Central Africa'
SELECT AVG(LifeExpectancy) FROM country WHERE Region = 'Central Africa'
SELECT Name FROM country WHERE Continent = 'Asia' ORDER BY LifeExpectancy LIMIT 1
SELECT Name FROM country WHERE Continent = 'Asia' ORDER BY LifeExpectancy ASC LIMIT 1
SELECT SUM(T2.Population) AS TotalPopulation, MAX(T1.GNP) AS MaxGNP FROM country AS T1 JOIN city AS T2 ON T1.Code = T2.CountryCode WHERE T1.Continent = 'Asia'
SELECT SUM(c.Population) AS TotalPopulation, MAX(co.GNP) AS LargestGNP FROM country AS co JOIN city AS c ON co.Code = c.CountryCode WHERE co.Continent = 'Asia'
SELECT AVG(c LifeExpectancy) FROM country c WHERE c.Continent = 'Africa' AND c.GovernmentForm LIKE '%Republic%'
SELECT AVG(LifeExpectancy) FROM country WHERE Continent = 'Africa' AND GovernmentForm LIKE '%Republic%'
SELECT SUM(SurfaceArea) FROM country WHERE Continent IN ('Asia', 'Europe')
SELECT SUM(SurfaceArea) FROM country WHERE Continent IN ('Asia', 'Europe')
SELECT COUNT(*) FROM city WHERE District = 'Gelderland'
SELECT SUM(T1.Population) FROM city AS T1 JOIN country AS T2 ON SUBSTR(T1.Name, 1, LENGTH(T2.Name)) = T2.Name WHERE T1.District = 'Gelderland'
SELECT AVG(GNP) AS AverageGNP, SUM(Population) AS TotalPopulation FROM country WHERE GovernmentForm LIKE '%US territory%'
SELECT AVG(T2.GNP) AS MeanGNP, SUM(T1.Population) AS TotalPopulation FROM city AS T1 JOIN country AS T2 ON T1.CountryCode = T2.Code WHERE T2.Code IN ('UMI', 'VIR', 'VIQ', 'IOT', 'GU', 'MP', 'PR', 'AS')
SELECT COUNT(DISTINCT Language) FROM countrylanguage
SELECT COUNT(DISTINCT Language) FROM countrylanguage
SELECT COUNT(DISTINCT GovernmentForm) FROM country WHERE Continent = 'Africa'
SELECT COUNT(DISTINCT GovernmentForm) FROM country WHERE Continent = 'Africa'
SELECT COUNT(DISTINCT Language) FROM countrylanguage WHERE CountryCode = (SELECT Code FROM country WHERE Name = 'Aruba')
SELECT COUNT(DISTINCT CountryCode) FROM countrylanguage WHERE CountryCode = (SELECT Code FROM country WHERE Name = 'Aruba')
SELECT COUNT(*) FROM countrylanguage WHERE CountryCode = (SELECT Code FROM country WHERE Name = 'Afghanistan') AND IsOfficial = 'T'
SELECT COUNT(*) FROM countrylanguage WHERE CountryCode = (SELECT Code FROM country WHERE Name = 'Afghanistan') AND IsOfficial = 'T'
SELECT c.Name FROM country c JOIN countrylanguage cl ON c.Code = cl.CountryCode GROUP BY c.Code, c.Name ORDER BY COUNT(cl.Language) DESC LIMIT 1
SELECT T2.Name FROM countrylanguage AS T1 JOIN country AS T2 ON T1.CountryCode = T2.Code GROUP BY T2.Name ORDER BY COUNT(T1.Language) DESC LIMIT 1
SELECT T2.Continent FROM countrylanguage AS T1 JOIN country AS T2 ON T1.CountryCode = T2.Code GROUP BY T2.Continent ORDER BY COUNT(DISTINCT T1.Language) DESC LIMIT 1
SELECT c.Continent FROM country c JOIN countrylanguage cl ON c.Code = cl.CountryCode GROUP BY c.Continent ORDER BY COUNT(DISTINCT cl.Language) DESC LIMIT 1
SELECT COUNT(DISTINCT c1.Code) FROM country AS c1 JOIN countrylanguage AS cl1 ON c1.Code = cl1.CountryCode JOIN countrylanguage AS cl2 ON c1.Code = cl2.CountryCode WHERE cl1.Language = 'English' AND cl2.Language = 'Dutch' AND cl1.IsOfficial = 'T' AND cl2.IsOfficial = 'T'
SELECT COUNT(DISTINCT CountryCode) FROM countrylanguage WHERE Language = 'English' AND IsOfficial = 'T' UNION SELECT COUNT(DISTINCT CountryCode) FROM countrylanguage WHERE Language = 'Dutch' AND IsOfficial = 'T' GROUP BY CountryCode
SELECT DISTINCT c.Name FROM country c JOIN countrylanguage cl1 ON c.Code = cl1.CountryCode JOIN countrylanguage cl2 ON c.Code = cl2.CountryCode WHERE cl1.Language = 'English' AND cl2.Language = 'French' AND cl1.IsOfficial = 'T' AND cl2.IsOfficial = 'T'
SELECT DISTINCT c.Name FROM country c JOIN countrylanguage cl1 ON c.Code = cl1.CountryCode AND cl1.Language = 'English' JOIN countrylanguage cl2 ON c.Code = cl2.CountryCode AND cl2.Language = 'French'
SELECT DISTINCT c.Name FROM country c JOIN countrylanguage cl1 ON c.Code = cl1.CountryCode JOIN countrylanguage cl2 ON c.Code = cl2.CountryCode WHERE cl1.Language = 'English' AND cl1.IsOfficial = 'T' AND cl2.Language = 'French' AND cl2.IsOfficial = 'T'
SELECT DISTINCT c.Name FROM country c JOIN countrylanguage cl1 ON c.Code = cl1.CountryCode JOIN countrylanguage cl2 ON c.Code = cl2.CountryCode WHERE cl1.Language = 'English' AND cl1.IsOfficial = 'T' AND cl2.Language = 'French' AND cl2.IsOfficial = 'T'
SELECT COUNT(DISTINCT T2.Continent) FROM countrylanguage AS T1 JOIN country AS T2 ON T1.CountryCode = T2.Code WHERE T1.Language = 'Chinese' AND T1.IsOfficial = 'T'
SELECT COUNT(DISTINCT c.Continent) FROM country AS c JOIN countrylanguage AS cl ON c.Code = cl.CountryCode WHERE cl.Language = 'Chinese' AND cl.IsOfficial = 'T'
SELECT DISTINCT T3.Region FROM countrylanguage AS T1 JOIN country AS T2 ON T1.CountryCode = T2.Code JOIN country AS T3 ON T2.Code = T3.Code WHERE T1.Language = 'English' OR T1.Language = 'Dutch'
SELECT DISTINCT T2.Region FROM countrylanguage AS T1 JOIN country AS T2 ON T1.CountryCode = T2.Code WHERE T1.Language IN ('Dutch', 'English')
SELECT DISTINCT c.Name FROM country AS c JOIN countrylanguage AS cl ON c.Code = cl.CountryCode WHERE cl.Language IN ('English', 'Dutch') AND cl.IsOfficial = 'T'
SELECT DISTINCT c.Name FROM country AS c JOIN countrylanguage AS cl ON c.Code = cl.CountryCode WHERE cl.Language IN ('English', 'Dutch') AND cl.IsOfficial = 'T'
SELECT T3.Language FROM country AS T1 JOIN city AS T2 ON T1.Code = T2.CountryCode JOIN countrylanguage AS T3 ON T1.Code = T3.CountryCode WHERE T1.Continent = 'Asia' GROUP BY T3.Language ORDER BY SUM(T3.Percentage) DESC LIMIT 1
SELECT Language FROM countrylanguage WHERE CountryCode IN (SELECT Code FROM country WHERE Continent = 'Asia') GROUP BY Language ORDER BY COUNT(CountryCode) DESC LIMIT 1
SELECT DISTINCT T3.Language FROM country AS T1 JOIN countrylanguage AS T3 ON T1.Code = T3.CountryCode JOIN city AS T2 ON T1.Code = T2.CountryCode WHERE T1.GovernmentForm = 'Republic' AND T3.IsOfficial = 'F' GROUP BY T3.Language HAVING COUNT(T3.CountryCode) = 1
SELECT DISTINCT T2.Language FROM countrylanguage AS T2 JOIN country AS T1 ON T2.CountryCode = T1.Code WHERE T1.GovernmentForm = 'Republic' AND T2.IsOfficial = 'F' GROUP BY T2.Language HAVING COUNT(T2.CountryCode) = 1
SELECT city.Name, city.Population FROM city JOIN countrylanguage ON city.CountryCode = countrylanguage.CountryCode WHERE countrylanguage.Language = 'English' ORDER BY city.Population DESC LIMIT 1
SELECT T1.Name FROM city AS T1 JOIN countrylanguage AS T2 ON T1.CountryCode = T2.CountryCode WHERE T2.Language = 'English' ORDER BY T1.Population DESC LIMIT 1
SELECT c.Name, c.Population, c.LifeExpectancy FROM country c WHERE c.Continent = 'Asia' AND c.SurfaceArea = (SELECT MAX(SurfaceArea) FROM country WHERE Continent = 'Asia')
SELECT Name, Population, LifeExpectancy FROM country WHERE Continent = 'Asia' AND SurfaceArea = (SELECT MAX(SurfaceArea) FROM country WHERE Continent = 'Asia')
SELECT AVG(c LifeExpectancy) FROM country c JOIN countrylanguage cl ON c.Code = cl.CountryCode WHERE cl.Language = 'English' AND cl.IsOfficial = 'F'
SELECT AVG(c LifeExpectancy) FROM country c JOIN countrylanguage cl ON c.Code = cl.CountryCode WHERE cl.IsOfficial = 'F' AND cl.Language = 'English'
SELECT SUM(T1.Population) FROM city AS T1 JOIN country AS T2 ON T1.CountryCode = T2.Code WHERE T2.Code NOT IN (SELECT CountryCode FROM countrylanguage WHERE Language = 'English')
SELECT SUM(city.Population) FROM city JOIN country ON city.CountryCode = country.Code WHERE country.Code NOT IN (SELECT CountryCode FROM countrylanguage WHERE Language = 'English')
SELECT countrylanguage.Language FROM country JOIN countrylanguage ON country.Code = countrylanguage.CountryCode WHERE country.HeadOfState = 'Beatrix' AND countrylanguage.IsOfficial = 'T'
SELECT T3.Language FROM country AS T1 INNER JOIN city AS T2 ON T1.Code = T2.CountryCode INNER JOIN countrylanguage AS T3 ON T1.Code = T3.CountryCode WHERE T2.HeadOfState = 'Beatrix' AND T3.IsOfficial = 'T'
SELECT COUNT(DISTINCT Language) FROM countrylanguage WHERE CountryCode IN (SELECT Code FROM country WHERE IndepYear < 1930) AND IsOfficial = 'T'
SELECT COUNT(DISTINCT T2.Language) FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code = T2.CountryCode WHERE T1.IndepYear < 1930 AND T2.IsOfficial = 'T'
SELECT Code, Name, Continent FROM country WHERE Continent = 'Europe' INTERSECT SELECT Code, Name, Continent FROM country WHERE SurfaceArea > (SELECT MAX(SurfaceArea) FROM country WHERE Continent = 'Europe')
SELECT Code FROM country WHERE Continent = 'Europe' GROUP BY Code HAVING SUM(SurfaceArea) > (SELECT MAX(SurfaceArea) FROM country WHERE Continent = 'Europe')
SELECT C1.Name FROM country AS C1 INNER JOIN country AS C2 ON C1.Population >= C2.Population WHERE C2.Continent = 'Asia' AND C1.Continent = 'Africa'
SELECT C1.Name FROM country AS C1 WHERE C1.Continent = 'Africa' AND C1.Population < ALL ( SELECT C2.Population FROM country AS C2 WHERE C2.Continent = 'Asia' )
SELECT C1.Name FROM country AS C1 WHERE C1.Continent = 'Asia' AND C1.Population > ALL ( SELECT C2.Population FROM country AS C2 WHERE C2.Continent = 'Africa' )
SELECT c1.Name FROM country AS c1 WHERE c1.Continent = 'Asia' AND c1.Population > (SELECT c2.Population FROM country AS c2 WHERE c2.Continent = 'Africa' AND c2.Population > 0 ORDER BY c2.Population DESC LIMIT 1)
SELECT Code FROM country WHERE Code NOT IN (SELECT CountryCode FROM countrylanguage WHERE Language = 'English')
SELECT Code FROM country WHERE Code NOT IN (SELECT CountryCode FROM countrylanguage WHERE Language = 'English')
SELECT DISTINCT CountryCode FROM countrylanguage WHERE Language != 'English'
SELECT DISTINCT Code FROM country WHERE Code IN (SELECT CountryCode FROM countrylanguage WHERE Language != 'English')
SELECT DISTINCT c.Code FROM country c JOIN countrylanguage cl ON c.Code = cl.CountryCode WHERE cl.Language != 'English' AND c.GovernmentForm != 'Republic'
SELECT Code FROM country WHERE Code NOT IN (SELECT CountryCode FROM countrylanguage WHERE Language = 'English') AND GovernmentForm NOT LIKE '%Republic%'
SELECT DISTINCT c.Name FROM city c JOIN country co ON c.CountryCode = co.Code WHERE co.Continent = 'Europe' AND co.Code NOT IN (SELECT cl.CountryCode FROM countrylanguage cl WHERE cl.Language = 'English' AND cl.IsOfficial = 'T')
SELECT c.Name FROM city c JOIN country co ON c.CountryCode = co.Code JOIN countrylanguage cl ON co.Code = cl.CountryCode WHERE co.Continent = 'Europe' AND cl.Language = 'English' AND cl.IsOfficial = 'F'
SELECT DISTINCT c.Name FROM city c JOIN country co ON c.CountryCode = co.Code JOIN countrylanguage cl ON co.Code = cl.CountryCode WHERE co.Continent = 'Asia' AND cl.Language = 'Chinese' AND cl.IsOfficial = 'T'
SELECT DISTINCT c.Name FROM city c JOIN countryco l ON c.CountryCode = l.CountryCode JOIN countrylan gl ON l.CountryCode = gl.CountryCode WHERE c.CountryCode IN (SELECT CountryCode FROM country WHERE Continent = 'Asia') AND gl.Language = 'Chinese' AND gl.IsOfficial = 'T'
SELECT Name, IndepYear, SurfaceArea FROM country ORDER BY Population ASC LIMIT 1
SELECT Name, IndepYear, SurfaceArea FROM country WHERE Population = (SELECT MIN(Population) FROM country)
SELECT Population, Name, HeadOfState FROM country ORDER BY SurfaceArea DESC LIMIT 1
SELECT Name, Population, HeadOfState FROM country ORDER BY SurfaceArea DESC LIMIT 1
SELECT c.Name, COUNT(cl.CountryCode) FROM country c JOIN countrylanguage cl ON c.Code = cl.CountryCode GROUP BY c.Code HAVING COUNT(cl.CountryCode) >= 3
SELECT T2.Name, COUNT(T1.Language) AS NumberOfLanguages FROM countrylanguage AS T1 JOIN country AS T2 ON T1.CountryCode = T2.Code GROUP BY T2.Code HAVING COUNT(T1.Language) > 2
SELECT District, COUNT(*) AS NumberOfCities FROM city WHERE Population > (SELECT AVG(Population) FROM city) GROUP BY District
SELECT District, COUNT(*) AS NumberOfCities FROM city WHERE Population > (SELECT AVG(Population) FROM city) GROUP BY District
SELECT GovernmentForm, SUM(Population) AS TotalPopulation FROM country WHERE LifeExpectancy > 72 GROUP BY GovernmentForm
SELECT T1.GovernmentForm, SUM(T2.Population) AS TotalPopulation FROM country AS T1 JOIN city AS T2 ON T1.Code = T2.CountryCode JOIN countrylanguage AS T3 ON T1.Code = T3.CountryCode WHERE CAST(SUBSTR(T3.IsOfficial, 1, 1) AS INTEGER) = 1 AND T1.LifeExpectancy > 72 GROUP BY T1.GovernmentForm
SELECT c.Continent, AVG(c.LifeExpectancy) AS AverageLifeExpectancy, SUM(c.Population) AS TotalPopulation FROM country c GROUP BY c.Continent HAVING AVG(c.LifeExpectancy) < 72
SELECT T1.Continent, SUM(T2.Population) AS TotalPopulation, AVG(T2.LifeExpectancy) AS AverageLifeExpectancy FROM country AS T1 JOIN city AS T2 ON T1.Code = T2.CountryCode GROUP BY T1.Continent HAVING AVG(T2.LifeExpectancy) < 72
SELECT Name, SurfaceArea FROM country ORDER BY SurfaceArea DESC LIMIT 5
SELECT Name, SurfaceArea FROM country ORDER BY SurfaceArea DESC LIMIT 5
SELECT Name FROM country ORDER BY Population DESC LIMIT 3
SELECT Name FROM country ORDER BY Population DESC LIMIT 3
SELECT Name FROM country ORDER BY Population ASC LIMIT 3
SELECT Name FROM country ORDER BY Population LIMIT 3
SELECT COUNT(*) FROM country WHERE Continent = 'Asia'
SELECT COUNT(*) FROM country WHERE Continent = 'Asia'
SELECT Name FROM country WHERE Continent = 'Europe' AND Population = 80000
SELECT Name FROM country WHERE Continent = 'Europe' AND Population = 80000
SELECT SUM(c.Population) AS TotalPopulation, AVG(co.SurfaceArea) AS AverageArea FROM country AS c JOIN continent AS ct ON ct.Code = c.Code WHERE ct.Name = 'North America' AND c.SurfaceArea > 3000
SELECT SUM(T2.Population) AS TotalPopulation, AVG(T1.SurfaceArea) AS AverageSurfaceArea FROM country AS T1 JOIN city AS T2 ON T1.Code = T2.CountryCode WHERE T1.Continent = 'North America' AND T1.SurfaceArea > 3000
SELECT Name FROM city WHERE Population BETWEEN 160000 AND 900000
SELECT Name FROM city WHERE Population BETWEEN 160000 AND 900000
SELECT Language FROM countrylanguage WHERE IsOfficial = 'T' GROUP BY Language ORDER BY COUNT(Code) DESC LIMIT 1
SELECT Language FROM countrylanguage WHERE CountryCode IN (SELECT Code FROM country) GROUP BY Language ORDER BY COUNT(Code) DESC LIMIT 1
SELECT c.Name, cl.Language, cl.Percentage FROM countrylanguage cl JOIN country c ON cl.CountryCode = c.Code WHERE cl.Percentage = ( SELECT MAX(Percentage) FROM countrylanguage WHERE CountryCode = cl.CountryCode )
SELECT T1.Code, T2.Language FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code = T2.CountryCode WHERE T2.Percentage = ( SELECT MAX(Percentage) FROM countrylanguage AS T3 WHERE T3.CountryCode = T2.CountryCode )
SELECT COUNT(*) FROM countrylanguage WHERE Language = 'Spanish' AND IsOfficial = 'T' OR Language = 'Spanish' AND Percentage = (SELECT MAX(Percentage) FROM countrylanguage WHERE Language = 'Spanish') AND CountryCode IN (SELECT Code FROM country)
SELECT COUNT(*) FROM countrylanguage WHERE Language = 'Spanish' AND IsOfficial = 'T'
SELECT Code FROM country WHERE Code IN (SELECT CountryCode FROM countrylanguage WHERE Language = 'Spanish' AND Percentage = (SELECT MAX(Percentage) FROM countrylanguage WHERE Language = 'Spanish'))
SELECT Code FROM country WHERE Code IN (SELECT CountryCode FROM countrylanguage WHERE Language = 'Spanish' AND IsOfficial = 'T')
SELECT COUNT(DISTINCT Conductor_ID) FROM conductor
SELECT COUNT(DISTINCT Conductor_ID) FROM conductor
SELECT Name FROM conductor ORDER BY Age ASC
SELECT Name FROM conductor ORDER BY Age
SELECT Name FROM conductor WHERE Nationality != "USA"
SELECT Name FROM conductor WHERE Nationality != 'USA'
SELECT Record_Company FROM orchestra ORDER BY Year_of_Founded DESC
SELECT Record_Company FROM orchestra ORDER BY Year_of_Founded DESC
SELECT AVG(Attendance) FROM show WHERE If_first_show = 'Yes'
SELECT AVG(Attendance) FROM show
SELECT MAX(T2.Share), MIN(T2.Share) FROM performance AS T1 JOIN show AS T2 ON T1.Performance_ID = T2.Performance_ID WHERE T1.Type != 'Live final'
SELECT MAX(T2.Share), MIN(T2.Share) FROM performance AS T1 JOIN show AS T2 ON T1.Performance_ID = T2.Performance_ID WHERE T1.Type != 'Live final'
SELECT COUNT(DISTINCT Nationality) FROM conductor
SELECT COUNT(DISTINCT Nationality) FROM conductor
SELECT Name FROM conductor ORDER BY Year_of_Work DESC
SELECT Name FROM conductor ORDER BY Year_of_Work DESC
SELECT Name FROM conductor WHERE Year_of_Work = (SELECT MAX(Year_of_Work) FROM conductor)
SELECT Name FROM conductor WHERE Year_of_Work = (SELECT MAX(Year_of_Work) FROM conductor)
SELECT c.Name, o.Orchestra FROM conductor c JOIN orchestra o ON c.Conductor_ID = o.Conductor_ID
SELECT c.Name, o.Orchestra FROM conductor c JOIN orchestra o ON c.Conductor_ID = o.Conductor_ID
SELECT c.Name FROM conductor c JOIN orchestra o ON c.Conductor_ID = o.Conductor_ID GROUP BY c.Conductor_ID, c.Name HAVING COUNT(o.Orchestra_ID) > 1
SELECT Name FROM conductor WHERE Conductor_ID IN (SELECT Conductor_ID FROM orchestra GROUP BY Conductor_ID HAVING COUNT(Orchestra_ID) > 1)
SELECT c.Name FROM conductor c JOIN orchestra o ON c.Conductor_ID = o.Conductor_ID GROUP BY c.Conductor_ID, c.Name ORDER BY COUNT(o.Orchestra_ID) DESC LIMIT 1
SELECT c.Name FROM conductor c JOIN orchestra o ON c.Conductor_ID = o.Conductor_ID GROUP BY c.Conductor_ID ORDER BY COUNT(o.Orchestra_ID) DESC LIMIT 1
SELECT DISTINCT c.Name FROM conductor c JOIN orchestra o ON c.Conductor_ID = o.Conductor_ID WHERE o.Year_of_Founded > 2008
SELECT DISTINCT c.Name FROM conductor c JOIN orchestra o ON c.Conductor_ID = o.Conductor_ID WHERE o.Year_of_Founded > 2008
SELECT Record_Company, COUNT(*) FROM orchestra GROUP BY Record_Company
SELECT Record_Company, COUNT(*) FROM orchestra GROUP BY Record_Company
SELECT T2.Major_Record_Format, COUNT(*) AS Count FROM orchestra AS T1 JOIN performance AS T1 ON T1.Orchestra_ID = T1.Conductor_ID JOIN Major_Record_Format AS T2 ON T1.Major_Record_Format = T2.Major_Record_Format GROUP BY T2.Major_Record_Format ORDER BY Count ASC
SELECT Major_Record_Format FROM orchestra GROUP BY Major_Record_Format ORDER BY COUNT(*) DESC
SELECT Record_Company FROM orchestra GROUP BY Record_Company ORDER BY COUNT(*) DESC LIMIT 1
SELECT Record_Company FROM orchestra GROUP BY Record_Company ORDER BY COUNT(*) DESC LIMIT 1
SELECT Orchestra FROM orchestra WHERE Orchestra_ID NOT IN (SELECT Orchestra_ID FROM performance)
SELECT Orchestra FROM orchestra WHERE Orchestra_ID NOT IN (SELECT Orchestra_ID FROM performance)
SELECT Record_Company FROM orchestra WHERE Year_of_Founded < 2003 INTERSECT SELECT Record_Company FROM orchestra WHERE Year_of_Founded > 2003
SELECT T2.Record_Company FROM orchestra AS T1 JOIN performance AS T3 ON T1.Orchestra_ID = T3.Orchestra_ID JOIN orchestra AS T4 ON T3.Orchestra_ID = T4.Orchestra_ID JOIN performance AS T5 ON T4.Orchestra_ID = T5.Orchestra_ID JOIN conductor AS T6 ON T1.Conductor_ID = T6.Conductor_ID JOIN conductor AS T7 ON T4.Conductor_ID = T7.Conductor_ID JOIN orchestra AS T8 ON T3.Orchestra_ID = T8.Orchestra_ID JOIN orchestra AS T9 ON T5.Orchestra_ID = T9.Orchestra_ID JOIN performance AS T10 ON T8.Orchestra_ID = T10.Orchestra_ID JOIN performance AS T11 ON T9.Orchestra_ID = T11.Orchestra_ID JOIN conductor AS T12 ON T8.Conductor_ID = T12.Conductor_ID JOIN conductor AS T13 ON T9.Conductor_ID = T13.Conductor_ID WHERE T1.Year_of_Founded < 2003 AND T4.Year_of_Founded > 2003 AND T6.Conductor_ID = T7.Conductor_ID AND T8.Conductor_ID = T9.Conductor_ID AND T10.Year_of_Founded < 2003 AND T11.Year_of_Founded > 2003 GROUP BY T2.Record_Company
SELECT COUNT(*) FROM orchestra WHERE Major_Record_Format IN ("CD", "DVD")
SELECT COUNT(*) FROM orchestra WHERE Major_Record_Format IN ('CD', 'DVD')
SELECT o.Year_of_Founded FROM orchestra o JOIN performance p ON o.Orchestra_ID = p.Orchestra_ID GROUP BY o.Orchestra_ID HAVING COUNT(p.Performance_ID) > 1
SELECT Year_of_Founded FROM orchestra WHERE Orchestra_ID IN (SELECT Orchestra_ID FROM performance GROUP BY Orchestra_ID HAVING COUNT(*) > 1)
SELECT COUNT(*) FROM Highschooler
SELECT COUNT(*) FROM Highschooler
SELECT name, grade FROM Highschooler
SELECT name, grade FROM Highschooler
SELECT grade FROM Highschooler
SELECT ID, grade FROM Highschooler
SELECT grade FROM Highschooler WHERE name = 'Kyle'
SELECT grade FROM Highschooler WHERE name = 'Kyle'
SELECT name FROM Highschooler WHERE grade = 10
SELECT name FROM Highschooler WHERE grade = 10
SELECT ID FROM Highschooler WHERE name = 'Kyle'
SELECT ID FROM Highschooler WHERE name = 'Kyle'
SELECT COUNT(*) FROM Highschooler WHERE grade IN (9, 10)
SELECT COUNT(*) FROM Highschooler WHERE grade IN (9, 10)
SELECT grade , COUNT(*) FROM Highschooler GROUP BY grade
SELECT grade , COUNT(*) FROM Highschooler GROUP BY grade
SELECT grade FROM Highschooler GROUP BY grade ORDER BY COUNT(*) DESC LIMIT 1
SELECT grade FROM Highschooler GROUP BY grade ORDER BY COUNT(*) DESC LIMIT 1
SELECT grade FROM Highschooler GROUP BY grade HAVING COUNT(ID) >= 4
SELECT grade FROM Highschooler GROUP BY grade HAVING COUNT(*) >= 4
SELECT F.student_id, COUNT(F.friend_id) AS num_of_friends FROM Friend F GROUP BY F.student_id
SELECT student_id, COUNT(friend_id) AS num_friends FROM Friend GROUP BY student_id
SELECT H.name, COUNT(F.friend_id) AS num_friends FROM Highschooler H JOIN Friend F ON H.ID = F.student_id GROUP BY H.ID, H.name
SELECT h.name, COUNT(f.friend_id) AS friend_count FROM Highschooler h JOIN Friend f ON h.ID = f.student_id GROUP BY h.ID
SELECT h.name FROM Highschooler h JOIN Friend f ON h.ID = f.student_id GROUP BY f.student_id ORDER BY COUNT(f.friend_id) DESC LIMIT 1
SELECT name FROM Highschooler WHERE ID = (SELECT student_id FROM Friend GROUP BY student_id ORDER BY COUNT(friend_id) DESC LIMIT 1)
SELECT h.name FROM Highschooler h JOIN Friend f ON h.ID = f.student_id GROUP BY h.ID, h.name HAVING COUNT(f.friend_id) >= 3
SELECT h.name FROM Highschooler h JOIN Friend f ON h.ID = f.student_id WHERE f.friend_id IN (SELECT friend_id FROM Friend) GROUP BY h.ID,h.name HAVING COUNT(f.friend_id) >= 3
SELECT H.name FROM Highschooler H JOIN Friend F ON H.ID = F.friend_id WHERE F.student_id = (SELECT ID FROM Highschooler WHERE name = 'Kyle')
SELECT H.name FROM Highschooler H JOIN Friend F ON H.ID = F.friend_id WHERE F.student_id = (SELECT ID FROM Highschooler WHERE name = 'Kyle')
SELECT COUNT(*) FROM Friend WHERE student_id = (SELECT ID FROM Highschooler WHERE name = 'Kyle')
SELECT COUNT(*) FROM Friend WHERE student_id = (SELECT ID FROM Highschooler WHERE name = 'Kyle')
SELECT ID FROM Highschooler WHERE ID NOT IN (SELECT friend_id FROM Friend)
SELECT ID FROM Highschooler WHERE ID NOT IN (SELECT friend_id FROM Friend)
SELECT name FROM Highschooler WHERE ID NOT IN (SELECT student_id FROM Friend)
SELECT name FROM Highschooler WHERE ID NOT IN (SELECT friend_id FROM Friend WHERE student_id IN (SELECT student_id FROM Friend))
SELECT DISTINCT F.student_id FROM Friend F JOIN Likes L ON F.student_id = L.student_id WHERE F.friend_id = L.liked_id
SELECT DISTINCT F.student_id FROM Friend F JOIN Likes L ON F.student_id = L.student_id
SELECT H.name FROM Highschooler H JOIN Friend F ON H.ID = F.student_id JOIN Likes L ON H.ID = L.student_id
SELECT H.name FROM Highschooler H JOIN Friend F ON H.ID = F.student_id JOIN Likes L ON H.ID = L.student_id
SELECT student_id, COUNT(liked_id) AS num_likes FROM Likes GROUP BY student_id
SELECT student_id, COUNT(liked_id) AS likes_count FROM Likes GROUP BY student_id
SELECT H.name, COUNT(L.student_id) FROM Highschooler H JOIN Likes L ON H.ID = L.student_id GROUP BY H.ID, H.name
SELECT H.name, COUNT(L.student_id) FROM Highschooler H JOIN Likes L ON H.ID = L.student_id GROUP BY H.ID, H.name
SELECT H.name FROM Highschooler H JOIN Likes L ON H.ID = L.student_id GROUP BY H.ID ORDER BY COUNT(L.student_id) DESC LIMIT 1
SELECT name FROM Highschooler WHERE ID = (SELECT student_id FROM Likes GROUP BY student_id ORDER BY COUNT(liked_id) DESC LIMIT 1)
SELECT H.name FROM Highschooler H JOIN Likes L ON H.ID = L.student_id GROUP BY H.ID, H.name HAVING COUNT(L.liked_id) >= 2
SELECT H.name FROM Highschooler H JOIN Likes L ON H.ID = L.student_id GROUP BY H.name HAVING COUNT(L.liked_id) >= 2
SELECT h.name FROM Highschooler h JOIN Friend f ON h.ID = f.student_id WHERE h.grade > 5 AND f.student_id IN (SELECT student_id FROM Friend GROUP BY student_id HAVING COUNT(friend_id) >= 2)
SELECT H.name FROM Highschooler H JOIN Friend F ON H.ID = F.student_id WHERE H.grade > 5 AND F.student_id IN (SELECT student_id FROM Friend GROUP BY student_id HAVING COUNT(friend_id) >= 2)
SELECT COUNT(*) FROM Likes WHERE student_id = (SELECT ID FROM Highschooler WHERE name = 'Kyle')
SELECT COUNT(*) FROM Likes WHERE student_id = (SELECT ID FROM Highschooler WHERE name = 'Kyle')
SELECT AVG(grade) FROM Highschooler WHERE ID IN (SELECT friend_id FROM Friend)
SELECT AVG(grade) FROM Highschooler WHERE ID IN (SELECT friend_id FROM Friend)
SELECT MIN(grade) FROM Highschooler WHERE ID NOT IN (SELECT friend_id FROM Friend)
SELECT MIN(grade) FROM Highschooler WHERE ID NOT IN (SELECT friend_id FROM Friend)
SELECT DISTINCT O.state FROM Owners O JOIN Professionals P ON O.state = P.state
SELECT DISTINCT o.state, p.state FROM Owners o JOIN Professionals p ON o.state = p.state
SELECT AVG(DATEDIFF(CURRENT_DATE, date_of_birth)) AS average_age FROM Dogs WHERE dog_id IN (SELECT dog_id FROM Treatments)
SELECT AVG(DATEDIFF(CURRENT_DATE, date_of_birth)) AS average_age FROM Dogs JOIN Treatments ON Dogs.dog_id = Treatments.dog_id
SELECT professional_id, last_name, cell_number FROM Professionals WHERE state = 'IN' UNION SELECT professional_id, last_name, cell_number FROM Treatments GROUP BY professional_id HAVING COUNT(dog_id) > 2
SELECT T.professional_id, P.last_name, P.cell_number FROM Professionals P JOIN Treatments T ON P.professional_id = T.professional_id WHERE P.state = 'Indiana' GROUP BY T.professional_id, P.last_name, P.cell_number HAVING COUNT(T.treatment_id) > 2 UNION SELECT T.professional_id, P.last_name, P.cell_number FROM Professionals P JOIN Treatments T ON P.professional_id = T.professional_id WHERE P.state != 'Indiana' GROUP BY T.professional_id, P.last_name, P.cell_number HAVING COUNT(T.treatment_id) > 2
SELECT DISTINCT d.name FROM Dogs d JOIN Treatments t ON d.dog_id = t.dog_id GROUP BY d.dog_id, d.name HAVING SUM(t.cost_of_treatment) <= 1000
SELECT DISTINCT d.name FROM Dogs d JOIN Treatments t ON d.dog_id = t.dog_id GROUP BY d.dog_id, d.name HAVING SUM(t.cost_of_treatment) <= 1000
SELECT first_name FROM Owners WHERE first_name NOT IN (SELECT name FROM Dogs) UNION SELECT first_name FROM Professionals WHERE first_name NOT IN (SELECT name FROM Dogs)
SELECT first_name FROM Owners WHERE first_name NOT IN (SELECT name FROM Dogs) UNION SELECT first_name FROM Professionals WHERE first_name NOT IN (SELECT name FROM Dogs)
SELECT professional_id, role_code, email_address FROM Professionals WHERE professional_id NOT IN (SELECT professional_id FROM Treatments)
SELECT professional_id, role_code, email_address FROM Professionals WHERE professional_id NOT IN (SELECT professional_id FROM Treatments)
SELECT o.owner_id, o.first_name, o.last_name FROM Owners o JOIN Dogs d ON o.owner_id = d.owner_id GROUP BY o.owner_id, o.first_name, o.last_name ORDER BY COUNT(d.dog_id) DESC LIMIT 1
SELECT o.owner_id, o.first_name, o.last_name FROM Owners o JOIN Dogs d ON o.owner_id = d.owner_id GROUP BY o.owner_id, o.first_name, o.last_name ORDER BY COUNT(d.dog_id) DESC LIMIT 1
SELECT T.professional_id, P.role_code, P.first_name FROM Treatments T JOIN Professionals P ON T.professional_id = P.professional_id GROUP BY T.professional_id, P.role_code, P.first_name HAVING COUNT(T.treatment_id) >= 2
SELECT professional_id, role_code, first_name FROM Professionals WHERE professional_id IN ( SELECT professional_id FROM Treatments GROUP BY professional_id HAVING COUNT(treatment_id) >= 2 )
SELECT B.breed_name FROM Breeds B JOIN Dogs D ON B.breed_code = D.breed_code GROUP BY B.breed_name ORDER BY COUNT(D.dog_id) DESC LIMIT 1
SELECT breed_name FROM Breeds WHERE breed_code = (SELECT breed_code FROM Dogs GROUP BY breed_code ORDER BY COUNT(*) DESC LIMIT 1)
SELECT o.owner_id, o.last_name FROM Owners o JOIN Dogs d ON o.owner_id = d.owner_id JOIN Treatments t ON d.dog_id = t.dog_id GROUP BY o.owner_id, o.last_name ORDER BY COUNT(t.treatment_id) DESC LIMIT 1
SELECT o.owner_id, o.last_name FROM Owners o JOIN ( SELECT dog_id, SUM(cost_of_treatment) as total_cost FROM Treatments GROUP BY dog_id ORDER BY total_cost DESC LIMIT 1 ) t ON o.owner_id = (SELECT owner_id FROM Dogs WHERE dog_id = t.dog_id)
SELECT T3.treatment_type_description FROM Treatments AS T1 JOIN Treatment_Types AS T3 ON T1.treatment_type_code = T3.treatment_type_code GROUP BY T1.treatment_type_code ORDER BY SUM(T1.cost_of_treatment) ASC LIMIT 1
SELECT T4.treatment_type_description FROM Treatments AS T1 JOIN Treatment_Types AS T4 ON T1.treatment_type_code = T4.treatment_type_code GROUP BY T1.treatment_type_code ORDER BY SUM(T1.cost_of_treatment) ASC LIMIT 1
SELECT o.owner_id, o.zip_code FROM Owners o JOIN Dogs d ON o.owner_id = d.owner_id JOIN Treatments t ON d.dog_id = t.dog_id GROUP BY o.owner_id, o.zip_code ORDER BY SUM(t.cost_of_treatment) DESC LIMIT 1
SELECT o.owner_id, o.zip_code FROM Owners o JOIN Dogs d ON o.owner_id = d.owner_id JOIN Treatments t ON d.dog_id = t.dog_id GROUP BY o.owner_id, o.zip_code ORDER BY SUM(t.cost_of_treatment) DESC LIMIT 1
SELECT T.professional_id, T.cell_number FROM ( SELECT professional_id, COUNT(DISTINCT treatment_type_code) AS treatment_count FROM Treatments GROUP BY professional_id HAVING COUNT(DISTINCT treatment_type_code) >= 2 ) AS T JOIN Professionals P ON T.professional_id = P.professional_id
SELECT professional_id, cell_number FROM Professionals WHERE professional_id IN ( SELECT professional_id FROM Treatments GROUP BY professional_id HAVING COUNT(DISTINCT treatment_type_code) >= 2 )
SELECT DISTINCT p.first_name, p.last_name FROM Professionals p JOIN Treatments t ON p.professional_id = t.professional_id WHERE t.cost_of_treatment < (SELECT AVG(cost_of_treatment) FROM Treatments)
SELECT DISTINCT p.first_name, p.last_name FROM Professionals p JOIN Treatments t ON p.professional_id = t.professional_id WHERE t.cost_of_treatment < (SELECT AVG(cost_of_treatment) FROM Treatments)
SELECT T.date_of_treatment, P.first_name FROM Treatments T JOIN Professionals P ON T.professional_id = P.professional_id
SELECT T.date_of_treatment, P.first_name FROM Treatments T JOIN Professionals P ON T.professional_id = P.professional_id
SELECT T.cost_of_treatment, TT.treatment_type_description FROM Treatments T JOIN Treatment_Types TT ON T.treatment_type_code = TT.treatment_type_code
SELECT T.cost_of_treatment, TT.treatment_type_description FROM Treatments T JOIN Treatment_Types TT ON T.treatment_type_code = TT.treatment_type_code
SELECT O.first_name, O.last_name, D.size_code FROM Owners O JOIN Dogs D ON O.owner_id = D.owner_id
SELECT O.first_name, O.last_name, D.size_code FROM Owners O JOIN Dogs D ON O.owner_id = D.owner_id
SELECT Owners.first_name, Dogs.name FROM Owners JOIN Dogs ON Owners.owner_id = Dogs.owner_id
SELECT O.first_name, D.name FROM Owners O JOIN Dogs D ON O.owner_id = D.owner_id
SELECT d.name, t.date_of_treatment FROM Dogs d JOIN Breeds b ON d.breed_code = b.breed_code JOIN Treatments t ON d.dog_id = t.dog_id WHERE b.breed_code = ( SELECT breed_code FROM Dogs GROUP BY breed_code ORDER BY COUNT(*) ASC LIMIT 1 )
SELECT D.name, T.date_of_treatment FROM Dogs D JOIN Breeds B ON D.breed_code = B.breed_code JOIN Treatments T ON D.dog_id = T.dog_id WHERE B.breed_code = (SELECT breed_code FROM Dogs WHERE breed_code = (SELECT breed_code FROM (SELECT breed_code FROM Breeds ORDER BY COUNT(breed_code) ASC LIMIT 1)))
SELECT O.first_name, D.name FROM Owners O JOIN Dogs D ON O.owner_id = D.owner_id WHERE O.state = 'Virginia'
SELECT DISTINCT O.first_name, D.name FROM Owners O JOIN Dogs D ON O.owner_id = D.owner_id WHERE O.state = 'Virginia'
SELECT d.date_arrived, d.date_departed FROM Dogs d JOIN Treatments t ON d.dog_id = t.dog_id
SELECT d.date_arrived, d.date_departed FROM Dogs d JOIN Treatments t ON d.dog_id = t.dog_id
SELECT DISTINCT o.last_name FROM Owners o JOIN Dogs d ON o.owner_id = d.owner_id WHERE d.date_of_birth = (SELECT MIN(date_of_birth) FROM Dogs)
SELECT O.last_name FROM Owners O JOIN Dogs D ON O.owner_id = D.owner_id WHERE D.date_of_birth = (SELECT MIN(date_of_birth) FROM Dogs)
SELECT email_address FROM Professionals WHERE state = 'HI' OR state = 'WI'
SELECT email_address FROM Professionals WHERE state = 'Hawaii' OR state = 'Wisconsin'
SELECT date_arrived, date_departed FROM Dogs
SELECT date_arrived, date_departed FROM Dogs
SELECT COUNT(DISTINCT dog_id) FROM Treatments
SELECT COUNT(DISTINCT dog_id) FROM Treatments
SELECT COUNT(DISTINCT professional_id) FROM Treatments
SELECT COUNT(DISTINCT professional_id) FROM Treatments
SELECT role_code, street, city, state FROM Professionals WHERE city LIKE '%West%'
SELECT role_code, street, city, state FROM Professionals WHERE city LIKE '%West%'
SELECT first_name, last_name, email_address FROM Owners WHERE state LIKE '%North%'
SELECT first_name, last_name, email_address FROM Owners WHERE state LIKE '%North%'
SELECT COUNT(*) FROM Dogs WHERE age < (SELECT AVG(age) FROM Dogs)
SELECT COUNT(*) FROM Dogs WHERE age < (SELECT AVG(age) FROM Dogs)
SELECT MAX(cost_of_treatment) FROM Treatments
SELECT MAX(cost_of_treatment) FROM Treatments WHERE cost_of_treatment = (SELECT MAX(date_of_treatment) FROM Treatments)
SELECT COUNT(*) FROM Dogs WHERE dog_id NOT IN (SELECT dog_id FROM Treatments)
SELECT COUNT(*) FROM Dogs WHERE dog_id NOT IN (SELECT dog_id FROM Treatments)
SELECT COUNT(*) FROM Owners WHERE NOT EXISTS (SELECT 1 FROM Dogs WHERE Dogs.owner_id = Owners.owner_id)
SELECT COUNT(*) FROM Owners WHERE owner_id NOT IN (SELECT owner_id FROM Dogs)
SELECT COUNT(*) FROM Professionals WHERE professional_id NOT IN (SELECT professional_id FROM Treatments)
SELECT COUNT(*) FROM Professionals WHERE professional_id NOT IN (SELECT professional_id FROM Treatments)
SELECT name, age, weight FROM Dogs WHERE abandoned_yn = '1'
SELECT name, age, weight FROM Dogs WHERE abandoned_yn = '1'
SELECT AVG(strftime('%Y', 'now') - strftime('%Y', date_of_birth)) AS average_age FROM Dogs
SELECT AVG(strftime('%Y', 'now') - strftime('%Y', date_of_birth)) AS average_age FROM Dogs
SELECT MAX(date_arrived - date_of_birth) AS age FROM Dogs
SELECT MAX(date_arrived) - MIN(date_of_birth) AS age FROM Dogs
SELECT charge_type, charge_amount FROM Charges
SELECT charge_type, charge_amount FROM Charges
SELECT MAX(charge_amount) FROM Charges WHERE charge_type = (SELECT charge_type FROM Charges ORDER BY charge_amount DESC LIMIT 1)
SELECT MAX(charge_amount) FROM Charges WHERE charge_type = (SELECT charge_type FROM Charges ORDER BY charge_amount DESC LIMIT 1)
SELECT email_address, cell_number, home_phone FROM Professionals
SELECT first_name, last_name, email_address, home_phone, cell_number FROM Professionals
SELECT DISTINCT b.breed_name, s.size_description FROM Breeds b JOIN Dogs d ON b.breed_code = d.breed_code JOIN Sizes s ON d.size_code = s.size_code
SELECT DISTINCT T1.breed_name, T3.size_description FROM Breeds AS T1 JOIN Dogs AS T2 ON T1.breed_code = T2.breed_code JOIN Sizes AS T3 ON T3.size_code = T2.size_code
SELECT DISTINCT P.first_name, T.treatment_type_description FROM Professionals P JOIN Treatments T ON P.professional_id = T.professional_id
SELECT P.first_name, T.treatment_type_description FROM Professionals P JOIN Treatments T ON P.professional_id = T.professional_id
SELECT COUNT(*) FROM singer
SELECT COUNT(*) FROM singer
SELECT Name FROM singer ORDER BY Net_Worth_Millions ASC
SELECT Name FROM singer ORDER BY Net_Worth_Millions ASC
SELECT Birth_Year, Citizenship FROM singer
SELECT Birth_Year, Citizenship FROM singer
SELECT Name FROM singer WHERE Citizenship != "France"
SELECT Name FROM singer WHERE Citizenship != 'French'
SELECT Name FROM singer WHERE Birth_Year IN (1948, 1949)
SELECT Name FROM singer WHERE Birth_Year IN (1948, 1949)
SELECT Name FROM singer WHERE Net_Worth_Millions = (SELECT MAX(Net_Worth_Millions) FROM singer)
SELECT Name FROM singer WHERE Net_Worth_Millions = (SELECT MAX(Net_Worth_Millions) FROM singer)
SELECT Citizenship, COUNT(*) FROM singer GROUP BY Citizenship
SELECT Citizenship, COUNT(*) FROM singer GROUP BY Citizenship
SELECT Citizenship FROM singer GROUP BY Citizenship ORDER BY COUNT(*) DESC LIMIT 1
SELECT Citizenship FROM singer GROUP BY Citizenship ORDER BY COUNT(*) DESC LIMIT 1
SELECT Citizenship, MAX(Net_Worth_Millions) FROM singer GROUP BY Citizenship
SELECT Citizenship, MAX(Net_Worth_Millions) FROM singer GROUP BY Citizenship
SELECT song.Title, singer.Name FROM song JOIN singer ON song.Singer_ID = singer.Singer_ID
SELECT song.Title, singer.Name FROM song JOIN singer ON song.Singer_ID = singer.Singer_ID
SELECT DISTINCT T1.Name FROM singer AS T1 JOIN song AS T2 ON T1.Singer_ID = T2.Singer_ID WHERE T2.Sales > 300000
SELECT DISTINCT s.Name FROM singer s JOIN song sg ON s.Singer_ID = sg.Singer_ID WHERE sg.Sales > 300000
SELECT Name FROM singer WHERE Singer_ID IN (SELECT Singer_ID FROM song GROUP BY Singer_ID HAVING COUNT(Singer_ID) > 1)
SELECT Name FROM singer WHERE Singer_ID IN (SELECT Singer_ID FROM song GROUP BY Singer_ID HAVING COUNT(Singer_ID) > 1)
SELECT T1.Name, SUM(T2.Sales) FROM singer AS T1 JOIN song AS T2 ON T1.Singer_ID = T2.Singer_ID GROUP BY T1.Singer_ID, T1.Name
SELECT s.Name, SUM(song.Sales) AS Total_Sales FROM singer s JOIN song ON s.Singer_ID = song.Singer_ID GROUP BY s.Name
SELECT Name FROM singer WHERE Singer_ID NOT IN (SELECT Singer_ID FROM song)
SELECT Name FROM singer WHERE Singer_ID NOT IN (SELECT Singer_ID FROM song)
SELECT Citizenship FROM singer WHERE Birth_Year < 1945 INTERSECT SELECT Citizenship FROM singer WHERE Birth_Year > 1955
SELECT Citizenship FROM singer WHERE Birth_Year < 1945 INTERSECT SELECT Citizenship FROM singer WHERE Birth_Year > 1955
SELECT COUNT(DISTINCT feature_id) FROM Other_Available_Features
SELECT T2.feature_type_name FROM Other_Available_Features AS T1 JOIN Ref_Feature_Types AS T2 ON T1.feature_type_code = T2.feature_type_code WHERE T1.feature_name = 'AirCon'
SELECT Ref_Property_Types.property_type_description FROM Properties INNER JOIN Ref_Property_Types ON Properties.property_type_code = Ref_Property_Types.property_type_code
SELECT property_name FROM Properties WHERE property_type_code IN ('APT', 'HSE') AND room_count > 1
