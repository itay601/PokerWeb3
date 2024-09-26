// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.27;

contract Poker {
    struct Player {
        address payable playerAddress;
        bool isParticipating;
        uint256 chips;
        uint8[] hand; // Player's hand (card identifiers)
    }

    struct Game {
        uint256 gameId;
        address dealer;
        uint256 pot;
        uint256 buyIn;
        Player[] players;
        bool isActive;
        uint256 currentBet;
        uint8[] deck; // Card deck
        uint8[] communityCards; // Community cards
        GameState currentState;
    }

    enum GameState { PreFlop, Flop, Turn, River, End }

    mapping(uint256 => Game) public games;
    uint256 public gameCount;

    event GameCreated(uint256 indexed gameId, address indexed dealer, uint256 buyIn);
    event PlayerJoined(uint256 indexed gameId, address indexed player);
    event GameStarted(uint256 indexed gameId);
    event GameEnded(uint256 indexed gameId, address winner);
    event CardsDealt(uint256 indexed gameId, uint8[] communityCards);
    event PlayerAction(uint256 indexed gameId, address indexed player, string action, uint256 amount);

    modifier onlyDealer(uint256 _gameId) {
        require(msg.sender == games[_gameId].dealer, "Not the dealer");
        _;
    }

    modifier gameActive(uint256 _gameId) {
        require(games[_gameId].isActive, "Game is not active");
        _;
    }

    function createGame(uint256 _buyIn) external {
        gameCount++;
        Game storage newGame = games[gameCount];
        newGame.gameId = gameCount;
        newGame.dealer = msg.sender;
        newGame.buyIn = _buyIn;
        newGame.isActive = true;
        newGame.currentBet = 0;
        newGame.currentState = GameState.PreFlop;

        emit GameCreated(gameCount, msg.sender, _buyIn);
    }

    function joinGame(uint256 _gameId) external payable gameActive(_gameId) {
        Game storage game = games[_gameId];
        require(msg.value == game.buyIn, "Incorrect buy-in amount");
        
        game.players.push(Player({
            playerAddress: payable(msg.sender),
            isParticipating: true,
            chips: msg.value,
            hand: new uint8[](0) // Initialize empty hand
        }));
        
        game.pot += msg.value;

        emit PlayerJoined(_gameId, msg.sender);
    }

    function startGame(uint256 _gameId) external onlyDealer(_gameId) gameActive(_gameId) {
        shuffleAndDeal(_gameId);
        emit GameStarted(_gameId);
    }

    function shuffleAndDeal(uint256 _gameId) internal {
        Game storage game = games[_gameId];
        game.deck = createDeck();
        // Shuffle logic (omitted for brevity)
        
        // Deal cards to players
        for (uint256 i = 0; i < game.players.length; i++) {
            // Deal two cards to each player (omitted for brevity)
            // e.g., game.players[i].hand.push(dealCard());
        }
        
        emit CardsDealt(_gameId, game.communityCards);
    }

    function createDeck() internal pure returns (uint8[] memory) {
        uint8[] memory deck = new uint8[](52);
        for (uint8 i = 0; i < 52; i++) {
            deck[i] = i; // Assigning identifiers to cards
        }
        return deck;
    }

    function bet(uint256 _gameId, uint256 _amount) external gameActive(_gameId) {
        Game storage game = games[_gameId];
        require(_amount > game.currentBet, "Bet must be higher than current bet");
        // Check if player is participating and has enough chips (omitted for brevity)

        // Update pot and player chips (omitted for brevity)

        game.currentBet = _amount;
        emit PlayerAction(_gameId, msg.sender, "Bet", _amount);
    }

    function call(uint256 _gameId) external gameActive(_gameId) {
        Game storage game = games[_gameId];
        // Logic for calling the current bet (omitted for brevity)
        
        emit PlayerAction(_gameId, msg.sender, "Call", game.currentBet);
    }

    function Raise(uint256 _gameId, uint256 _amount) external gameActive(_gameId) {
        Game storage game = games[_gameId];
        require(_amount > game.currentBet, "Raise must be higher than current bet");
        
        // Update pot and player chips (omitted for brevity)

        game.currentBet = _amount;
        emit PlayerAction(_gameId, msg.sender, "Raise", _amount);
    }

    function fold(uint256 _gameId) external gameActive(_gameId) {
        Game storage game = games[_gameId];
        // Logic for folding (omitted for brevity)

        emit PlayerAction(_gameId, msg.sender, "Fold", 0);
    }

    function endGame(uint256 _gameId, address payable _winner) external onlyDealer(_gameId) gameActive(_gameId) {
        Game storage game = games[_gameId];
        game.isActive = false;

        _winner.transfer(game.pot);
        emit GameEnded(_gameId, _winner);
    }
}
