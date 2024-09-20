INSERT INTO User (UserId, Username, Password, Email, FirstName, LastName, RoleId)
SELECT %s, %s, %s, %s, %s, %s, %s
WHERE NOT EXISTS (
    SELECT 1 FROM User WHERE Username = %s
);