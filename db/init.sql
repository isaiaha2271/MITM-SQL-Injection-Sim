CREATE TABLE USERS (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    address VARCHAR(50) ,
    phoneNumber VARCHAR(50),
    licenseNumber VARCHAR(50),
    firstName VARCHAR(50) not NULL,
    lastName VARCHAR(50) not NULL
);


INSERT INTO USERS(username, password, firstName, lastName) VALUES
('admin', 'admin123', 'head', 'administrator'),
('test1', 'lebron', 'lebron', 'james');