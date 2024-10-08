INSERT INTO UserInvitation (Username, Email, FirstName, LastName, RoleId)
SELECT %s, %s, %s, %s, %s
WHERE NOT EXISTS (
    SELECT 1 FROM UserInvitation WHERE Email = %s
);