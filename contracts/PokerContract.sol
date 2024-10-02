// SPDX-License-Identifier: MIT
pragma solidity ^0.8.27;

contract Poker {
    struct Player {
        address payable playerAddress;
        bool isParticipating;
        uint256 chips;
        uint8[] hand;
        bool hasActed;
        bool showCards;
    }

    struct Game {
        uint256 gameId;
        address dealer;
        uint256 pot;
        uint256 buyIn;
        Player[] players;
        bool isActive;
        uint256 currentBet;
        uint8[] deck;
        uint8[] communityCards;
        GameState currentState;
        uint256 lastActionTimestamp;
        uint256 currentPlayerIndex;
        uint256 roundStartPlayerIndex;
        uint256 gameStartTime;
        uint256 roundEndTime;
    }

    enum GameState { PreFlop, Flop, Turn, River, End }

    mapping(uint256 => Game) public games;
    mapping(uint256 => mapping(address => Player)) public players;  
    uint256 public gameCount;

    uint256 private constant MAX_PLAYERS = 3;
    uint256 private constant TIMEOUT_DURATION = 5 minutes;
    uint256 private constant ROUND_DURATION = 10 minutes;

    bool private locked;

    event GameCreated(uint256 indexed gameId, address indexed dealer, uint256 buyIn);
    event PlayerJoined(uint256 indexed gameId, address indexed player);
    event GameStarted(uint256 indexed gameId);
    event CardsDealt(uint256 indexed gameId);
    event PlayerAction(uint256 indexed gameId, address indexed player, string action, uint256 amount);
    event GameStateChanged(uint256 indexed gameId, GameState newState);
    event GameEnded(uint256 indexed gameId, address winner);
    event RoundEnded(uint256 indexed gameId, GameState newState);
    event CommunityCardsRevealed(uint256 indexed gameId, uint8[] cards);
    event PlayerHandRevealed(uint256 indexed gameId, address indexed player, uint8[] hand);

    modifier noReentrant() {
        require(!locked, "No re-entrancy");
        locked = true;
        _;
        locked = false;
    }

    modifier onlyDealer(uint256 _gameId) {
        require(msg.sender == games[_gameId].dealer, "Not the dealer");
        _;
    }

    modifier gameActive(uint256 _gameId) {
        require(games[_gameId].isActive, "Game is not active");
        _;
    }

    modifier onlyParticipating(uint256 _gameId) {
        require(isParticipatingPlayer(_gameId, msg.sender), "Not a participating player");
        _;
    }

    modifier onlyCurrentPlayer(uint256 _gameId) {
        Game storage game = games[_gameId];
        require(msg.sender == game.players[game.currentPlayerIndex].playerAddress, "Not your turn");
        _;
    }

    constructor() {
        gameCount = 0;
        locked = false;
    }
    
    function getCurrentState(uint256 _gameId) public view returns (GameState currentState) {
        return games[_gameId].currentState;
    }


    function createGame(uint256 _buyIn) external {
        require(_buyIn > 0, "Buy-in must be greater than zero");
        gameCount += 1;
        Game storage newGame = games[gameCount];
        newGame.gameId = gameCount;
        newGame.dealer = msg.sender;
        newGame.buyIn = _buyIn;
        newGame.isActive = true;
        newGame.currentBet = 0;
        newGame.currentState = GameState.PreFlop;
        newGame.lastActionTimestamp = block.timestamp;

        emit GameCreated(gameCount, msg.sender, _buyIn);
    }

    function joinGame(uint256 _gameId) external payable {
        Game storage game = games[_gameId];
        require(msg.value == game.buyIn, "Incorrect buy-in amount");
        require(game.players.length < MAX_PLAYERS, "Game is full");

        game.players.push(Player({
            playerAddress: payable(msg.sender),
            isParticipating: true,
            chips: msg.value,
            hand: new uint8[](0),
            hasActed: false,
            showCards: false
        }));

        game.pot += msg.value;
        emit PlayerJoined(_gameId, msg.sender);
    }

    function startGame(uint256 _gameId) external onlyDealer(_gameId) gameActive(_gameId) {
        Game storage game = games[_gameId];
        require(game.players.length >= 2, "Not enough players to start the game");
        shuffleAndDeal(_gameId);
        game.currentPlayerIndex = 0;
        game.roundStartPlayerIndex = 0;
        game.gameStartTime = block.timestamp;
        game.roundEndTime = block.timestamp + ROUND_DURATION;
        emit GameStarted(_gameId);
        emit GameStateChanged(_gameId, GameState.PreFlop);
    }

    function bet(uint256 _gameId, uint256 _amount) external gameActive(_gameId) onlyParticipating(_gameId) {
        Game storage game = games[_gameId];
        require(block.timestamp < game.roundEndTime, "Round has ended");
        require(_amount > game.currentBet, "Bet must be higher than current bet");
        Player storage player = getPlayer(_gameId, msg.sender);
        require(player.chips >= _amount, "Not enough chips");

        game.pot += _amount;
        player.chips -= _amount;
        game.currentBet = _amount;
        game.lastActionTimestamp = block.timestamp;
        player.hasActed = true;

        emit PlayerAction(_gameId, msg.sender, "Bet", _amount);
        nextPlayer(_gameId);
    }

    function call(uint256 _gameId) external gameActive(_gameId) onlyParticipating(_gameId) {
        Game storage game = games[_gameId];
        require(block.timestamp < game.roundEndTime, "Round has ended");
        Player storage player = getPlayer(_gameId, msg.sender);
        require(player.chips >= game.currentBet, "Not enough chips to call");

        uint256 callAmount = game.currentBet;
        player.chips -= callAmount;
        game.pot += callAmount;
        game.lastActionTimestamp = block.timestamp;
        player.hasActed = true;

        emit PlayerAction(_gameId, msg.sender, "Call", callAmount);
        nextPlayer(_gameId);
    }

    function raise_(uint256 _gameId, uint256 _amount) external gameActive(_gameId) onlyParticipating(_gameId) {
        Game storage game = games[_gameId];
        require(block.timestamp < game.roundEndTime, "Round has ended");
        require(_amount > game.currentBet, "Raise must be higher than current bet");
        Player storage player = getPlayer(_gameId, msg.sender);
        require(player.chips >= _amount, "Not enough chips to raise");

        game.pot += _amount;
        player.chips -= _amount;
        game.currentBet = _amount;
        game.lastActionTimestamp = block.timestamp;
        player.hasActed = true;

        emit PlayerAction(_gameId, msg.sender, "Raise", _amount);
        nextPlayer(_gameId);
    }

    function fold(uint256 _gameId) external gameActive(_gameId) onlyParticipating(_gameId)  {
        Game storage game = games[_gameId];
        require(block.timestamp < game.roundEndTime, "Round has ended");
        Player storage player = getPlayer(_gameId, msg.sender);
        player.isParticipating = false;
        game.lastActionTimestamp = block.timestamp;
        player.hasActed = true;

        emit PlayerAction(_gameId, msg.sender, "Fold", 0);
        nextPlayer(_gameId);
    }

    function nextPlayer(uint256 _gameId) internal {
        Game storage game = games[_gameId];
        uint256 nextPlayerIndex = (game.currentPlayerIndex + 1) % game.players.length;

        while (!game.players[nextPlayerIndex].isParticipating) {
            nextPlayerIndex = (nextPlayerIndex + 1) % game.players.length;
        }

        if (nextPlayerIndex == game.roundStartPlayerIndex || allPlayersActed(_gameId) || block.timestamp >= game.roundEndTime) {
            advanceGameState(_gameId);
        } else {
            game.currentPlayerIndex = nextPlayerIndex;
        }
    }

    function allPlayersActed(uint256 _gameId) internal view returns (bool) {
        Game storage game = games[_gameId];
        for (uint256 i = 0; i < game.players.length; i++) {
            if (game.players[i].isParticipating && !game.players[i].hasActed) {
                return false;
            }
        }
        return true;
    }

    function advanceGameState(uint256 _gameId) internal {
        Game storage game = games[_gameId];
        
        if (game.currentState == GameState.PreFlop) {
            game.currentState = GameState.Flop;
            dealCommunityCards(game, 3);
            revealCommunityCards(_gameId, 3);
        } else if (game.currentState == GameState.Flop) {
            game.currentState = GameState.Turn;
            dealCommunityCards(game, 1);
            revealCommunityCards(_gameId, 4);
        } else if (game.currentState == GameState.Turn) {
            game.currentState = GameState.River;
            dealCommunityCards(game, 1);
            revealCommunityCards(_gameId, 5);
        } else if (game.currentState == GameState.River) {
            game.currentState = GameState.End;
            revealAllHands(_gameId);
            endGame(_gameId);
            return;
        }

        emit GameStateChanged(_gameId, game.currentState);
        emit RoundEnded(_gameId, game.currentState);
        resetRound(_gameId);
    }

    function resetRound(uint256 _gameId) internal {
        Game storage game = games[_gameId];
        game.currentBet = 0;
        game.roundStartPlayerIndex = (game.roundStartPlayerIndex + 1) % game.players.length;
        game.currentPlayerIndex = game.roundStartPlayerIndex;
        game.roundEndTime = block.timestamp + ROUND_DURATION;

        for (uint256 i = 0; i < game.players.length; i++) {
            if (game.players[i].isParticipating) {
                game.players[i].hasActed = false;
            }
        }
    }

    function endGame(uint256 _gameId) internal {
        Game storage game = games[_gameId];
        require(game.isActive, "Game is not active");
        
        game.isActive = false;
        address payable winner = determineWinner(_gameId);
        
        if (winner != address(0)) {
            uint256 winnings = game.pot;
            game.pot = 0;
            
            // Use transfer instead of call
            winner.transfer(winnings);
        }

        emit GameEnded(_gameId, winner);
    }

    function shuffleAndDeal(uint256 _gameId) internal {
        Game storage game = games[_gameId];
        game.deck = createDeck();
        shuffleDeck(game.deck);

        for (uint256 i = 0; i < game.players.length; i++) {
            if (game.players[i].isParticipating) {
                game.players[i].hand = new uint8[](2);
                game.players[i].hand[0] = dealCard(game);
                game.players[i].hand[1] = dealCard(game);
            }
        }

        emit CardsDealt(_gameId);
    }

    function dealCard(Game storage game) internal returns (uint8) {
        require(game.deck.length > 0, "No cards left to deal");
        uint8 card = game.deck[game.deck.length - 1];
        game.deck.pop();
        return card;
    }

    function dealCommunityCards(Game storage game, uint8 count) internal {
        for (uint8 i = 0; i < count; i++) {
            game.communityCards.push(dealCard(game));
        }
    }

    function createDeck() internal pure returns (uint8[] memory) {
        uint8[] memory deck = new uint8[](52);
        for (uint8 i = 0; i < 52; i++) {
            deck[i] = i;
        }
        return deck;
    }

    function shuffleDeck(uint8[] storage deck) internal {
        uint256 deckLength = deck.length;
        for (uint256 i = deckLength - 1; i > 0; i--) {
            uint256 j = uint256(keccak256(abi.encodePacked(block.prevrandao, block.timestamp, deck))) % (i + 1);
            (deck[i], deck[j]) = (deck[j], deck[i]); // Swap cards
        }   
    }

    function getPlayer(uint256 _gameId, address _player) internal view returns (Player storage) {
        Game storage game = games[_gameId];
        for (uint256 i = 0; i < game.players.length; i++) {
            if (game.players[i].playerAddress == _player) {
                return game.players[i];
            }
        }
        revert("Player not found");
    }

    function isParticipatingPlayer(uint256 _gameId, address _player) internal view returns (bool) {
        Game storage game = games[_gameId];
        for (uint256 i = 0; i < game.players.length; i++) {
            if (game.players[i].playerAddress == _player && game.players[i].isParticipating) {
                return true;
            }
        }
        return false;
    }

    function determineWinner(uint256 _gameId) internal view returns (address payable) {
        Game storage game = games[_gameId];
        address payable winner;
        uint256 highestRank = 0;

        for (uint256 i = 0; i < game.players.length; i++) {
            Player storage player = game.players[i];
            if (player.isParticipating) {
                uint256 playerRank = evaluateHand(player.hand, game.communityCards);
                if (playerRank > highestRank) {
                    highestRank = playerRank;
                    winner = player.playerAddress;
                }
            }
        }
        
        return winner;
    }
    
    function evaluateHand(uint8[] memory hand, uint8[] memory communityCards) internal pure returns (uint256) {
        // Combine hand and community cards
        uint8[] memory fullHand = new uint8[](hand.length + communityCards.length);
        for (uint8 i = 0; i < hand.length; i++) {
            fullHand[i] = hand[i];
        }
        for (uint8 j = 0; j < communityCards.length; j++) {
            fullHand[hand.length + j] = communityCards[j];
        }

        // Evaluate the best hand and return a rank
        // This is a placeholder; you should implement the actual poker hand ranking logic
        return simpleHandRank(fullHand);
    }

    function simpleHandRank(uint8[] memory cards) internal pure returns (uint256) {
        // Example ranking logic (simplified)
        // Assign a rank based on the highest card
        uint8 highestCard = 0;
        for (uint8 i = 0; i < cards.length; i++) {
            if (cards[i] > highestCard) {
                highestCard = cards[i];
            }
        }
        return uint256(highestCard); // Simplistic rank based on highest card
    }
     
    function revealCommunityCards(uint256 _gameId, uint8 count) internal {
        Game storage game = games[_gameId];
        require(count <= game.communityCards.length, "Not enough community cards to reveal");
        
        uint8[] memory revealedCards = new uint8[](count);
        for (uint8 i = 0; i < count; i++) {
            revealedCards[i] = game.communityCards[i];
        }
        
        emit CommunityCardsRevealed(_gameId, revealedCards);
    }

    function revealAllHands(uint256 _gameId) internal {
        Game storage game = games[_gameId];
        
        for (uint256 i = 0; i < game.players.length; i++) {
            Player storage player = game.players[i];
            if (player.isParticipating) {
                player.showCards = true;
                emit PlayerHandRevealed(_gameId, player.playerAddress, player.hand);
            }
        }
    }
}