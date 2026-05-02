CREATE TABLE USERS (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    address VARCHAR(50) ,
    phoneNumber VARCHAR(50) UNIQUE NOT NULL,
    licenseNumber VARCHAR(50) UNIQUE NOT NULL,
    firstname VARCHAR(50) NOT NULL,
    lastname VARCHAR(50) NOT NULL,
    company VARCHAR(50) NOT NULL
);

INSERT INTO USERS (username, password, address, phoneNumber, licenseNumber, firstname, lastname, company) VALUES
('admin', 'admin123', NULL, '000-0000', "administrator", 'administrator', 'administrator', "administrator"),
('jdoe1', 'dock@123A', '123 Main St', '555-0001', 'LIC0001', 'John', 'Doe', 'Oceanic Freight'),
('asmith2', 'wave!456B', '456 Oak St', '555-0002', 'LIC0002', 'Alice', 'Smith', 'BlueWave Logistics'),
('bwong3', 'atlas#789C', '789 Pine St', '555-0003', 'LIC0003', 'Brian', 'Wong', 'Atlas Shipping'),
('cjohnson4', 'harbor$321D', '101 Maple St', '555-0004', 'LIC0004', 'Chris', 'Johnson', 'HarborLine Transport'),
('dlee5', 'cargo%654E', '202 Elm St', '555-0005', 'LIC0005', 'Dana', 'Lee', 'Oceanic Freight'),
('egarcia6', 'ship^987F', '303 Birch St', '555-0006', 'LIC0006', 'Elena', 'Garcia', 'BlueWave Logistics'),
('fmartin7', 'route&159G', '404 Cedar St', '555-0007', 'LIC0007', 'Frank', 'Martin', 'Atlas Shipping'),
('gclark8', 'fleet*753H', '505 Walnut St', '555-0008', 'LIC0008', 'Grace', 'Clark', 'HarborLine Transport'),
('hlopez9', 'port(852I', '606 Chestnut St', '555-0009', 'LIC0009', 'Hector', 'Lopez', 'Oceanic Freight'),
('ikhan10', 'dock)951J', '707 Spruce St', '555-0010', 'LIC0010', 'Imran', 'Khan', 'BlueWave Logistics'),
('jyoung11', 'logi_357K', '808 Ash St', '555-0011', 'LIC0011', 'Jenna', 'Young', 'Atlas Shipping'),
('kpatel12', 'trans+258L', '909 Poplar St', '555-0012', 'LIC0012', 'Kiran', 'Patel', 'HarborLine Transport'),
('lwhite13', 'ship=147M', '111 Willow St', '555-0013', 'LIC0013', 'Liam', 'White', 'Oceanic Freight'),
('mhall14', 'cargo?369N', '222 Cherry St', '555-0014', 'LIC0014', 'Maya', 'Hall', 'BlueWave Logistics'),
('nallen15', 'route!741O', '333 Peach St', '555-0015', 'LIC0015', 'Noah', 'Allen', 'Atlas Shipping'),
('operez16', 'fleet@852P', '444 Plum St', '555-0016', 'LIC0016', 'Olivia', 'Perez', 'HarborLine Transport'),
('qreed17', 'port#963Q', '555 Apple St', '555-0017', 'LIC0017', 'Quinn', 'Reed', 'Oceanic Freight'),
('rturner18', 'dock$159R', '616 Pear St', '555-0018', 'LIC0018', 'Ryan', 'Turner', 'BlueWave Logistics'),
('sscott19', 'ship%753S', '777 Grape St', '555-0019', 'LIC0019', 'Sophie', 'Scott', 'Atlas Shipping'),
('tadams20', 'trans^258T', '888 Lemon St', '555-0020', 'LIC0020', 'Tyler', 'Adams', 'HarborLine Transport');