// Import the Hardhat library
const hre = require("hardhat");

async function main() {
    // Compile the contract (for edge case)
    await hre.run('compile');

    // Get the ContractFactory and Signers
    const Poker = await hre.ethers.getContractFactory("Poker");
    const [deployer] = await hre.ethers.getSigners();

    console.log("Deploying contracts with the account:", deployer.address);

    // Deploy the contract
    const pokerContract = await Poker.deploy();
    pokerContract.deployed;

    console.log("Poker contract deployed to: ", pokerContract.address);
}

// Execute the main function and handle errors
main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
