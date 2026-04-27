CREATE TABLE USERS (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    address VARCHAR(50) ,
    phoneNumber VARCHAR(50),
    licenseNumber VARCHAR(50),
    firstName VARCHAR(50),
    lastName VARCHAR(50)
);


INSERT INTO USERS(username, password) VALUES
('admin', 'admin123'),
('test1', 'lebron');