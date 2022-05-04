// Creates the items.composite collection using the items.leaf collection
db['items.leaf'].aggregate([
    {
        $addFields: {
            'monster': {
                $cond: {
                    if: {$eq: ['$location', null]},
                    then: null,
                    else: {
                        $arrayElemAt: [
                         {
                            $getField: {
                                field: 'monster',
                                input: {$arrayElemAt: ['$location', 0]}
                            }
                        },
                        1
                        ]
                    }
                }
            }
        }
    },
    {
        $addFields: {
            'difference': {
                $switch: {
                    branches: [
                        {
                            case: {
                                $regexMatch: {
                                    input: '$monster',
                                    regex: /NPC/
                                }
                            },
                            then: 'NPC'
                        },
                        {
                            case: {
                                $regexMatch: {
                                    input: '$monster',
                                    regex: /Player/
                                }
                            },
                            then: 'Player'
                        },
                        {
                            case: {
                                $regexMatch: {
                                    input: '$monster',
                                    regex: /Orb Shop/
                                }
                            },
                            then: 'Orb Shop'
                        }
                ],
                    default: 'Monster'
                }
            },
            'has_dye': {
                $cond: {
                    if: {$eq: ['$location', null]},
                    then: false,
                    else: {
                        $anyElementTrue: {
                            $map: {
                                input: '$location',
                                in: {
                                    $cond: {
                                        if: {
                                            $eq: ['$$this.dye', null]
                                        },
                                        then: null,
                                        else: '$$this.dye'
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    {
        $group: {
            _id: '$name',
            leaves: {
                $push: {
                    _id: '$_id',
                    difference: '$difference',
                    has_dye: '$has_dye'
                }
            }
        }
    },
    {$project: {_id: false, name: '$_id', leaves: '$leaves'}},
//    {$out: "items.composite"}
])