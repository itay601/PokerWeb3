const { ethers } = require("hardhat");

async function main() {
    const Poker = await ethers.getContractFactory("Poker");
    const contract = await Poker.deploy();

    console.log("contract deployed to:", await contract.getAddress());
}

main().catch((error) => {
    console.error("Error:", error);
    process.exitCode = 1;
});