const { ethers } = require("hardhat");

async function main() {
    // Get the list of Hardhat local accounts
    const accounts = await ethers.getSigners();

    console.log("Initial list of users with balances:");

    // Fetch and display initial balances
    for (const account of accounts) {
        const balance = await ethers.provider.getBalance(account.address);
        console.log(`Address: ${account.address}, Balance: ${(balance)} ETH`);
    }

    console.log("\nUpdating evaluations...");

    // Example evaluation logic
    const updatedEvaluations = accounts.map((account, index) => ({
        address: account.address,
        evaluation: Math.random() * 100, // Replace with your evaluation logic
    }));

    console.log("\nUpdated list of users with evaluations:");

    // Display updated evaluations
    updatedEvaluations.forEach(user => {
        console.log(`Address: ${user.address}, Evaluation: ${user.evaluation.toFixed(2)}`);
    });
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
