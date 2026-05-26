-- Sample: employee bonus stored procedure (used by tests)
CREATE PROCEDURE dbo.usp_ProcessEmployeeBonus
    @EmployeeID INT,
    @BonusAmount DECIMAL(18, 2)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @IsSuccess BIT = 0;
    DECLARE @ErrMsg NVARCHAR(4000);

    -- Process bonus inside TRY/CATCH
    BEGIN TRY
        UPDATE dbo.Employees
        SET Bonus = Bonus + @BonusAmount,
            LastModified = GETDATE()
        WHERE EmployeeID = @EmployeeID;

        INSERT INTO dbo.AuditLog (EmployeeID, LogMessage, CreatedDate)
        VALUES (@EmployeeID, CONCAT('Bonus processed: $', @BonusAmount), GETDATE());

        SET @IsSuccess = 1;
    END TRY
    BEGIN CATCH
        SET @IsSuccess = 0;
        SET @ErrMsg = ERROR_MESSAGE();
    END CATCH
END
